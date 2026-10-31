"""Database management and query operations for Empório da Música."""

import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd
from src.config import DB_PATH, DATA_DIR, format_currency_brl


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with Row factory enabled."""
    init_db_if_needed()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_if_needed(force: bool = False) -> None:
    """Initialize SQLite database from raw CSV files if not yet created."""
    if DB_PATH.exists() and not force:
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    tables = ["categories", "customers", "products", "orders", "order_items", "promotions"]
    for table_name in tables:
        csv_path = DATA_DIR / f"{table_name}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing required dataset: {csv_path}")

        df = pd.read_csv(csv_path)
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    # Create helpful indexes for performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_cat ON products(category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price_brl)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_tracking ON orders(tracking_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_promotions_prod ON promotions(product_id)")

    conn.commit()
    conn.close()


def calculate_payment_terms(price_brl: float) -> Dict[str, Any]:
    """Calculate payment options according to Empório da Música store policy:
    - PIX: 5% discount on table price.
    - Credit Card: up to 12x interest-free.
      * Parcela mínima:
        - 1x a 3x: min R$ 50,00
        - 4x a 6x: min R$ 80,00
        - 7x a 12x: min R$ 100,00
    """
    pix_price = round(price_brl * 0.95, 2)
    max_installments = 1

    if price_brl >= 100 * 7:
        # Check if can do up to 12x with min installment of 100
        max_installments = min(12, int(price_brl // 100))
    elif price_brl >= 80 * 4:
        max_installments = min(6, int(price_brl // 80))
    elif price_brl >= 50 * 2:
        max_installments = min(3, int(price_brl // 50))
    else:
        max_installments = 1

    installment_val = round(price_brl / max_installments, 2) if max_installments > 0 else price_brl

    return {
        "price_pix": pix_price,
        "price_pix_formatted": format_currency_brl(pix_price),
        "pix_discount_percent": 5,
        "max_installments": max_installments,
        "installment_value": installment_val,
        "installment_formatted": f"{max_installments}x de {format_currency_brl(installment_val)} sem juros",
    }


def search_products(
    query: Optional[str] = None,
    category_name: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = True,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Search products with category, price range, and stock filtering.
    Always includes active promotional pricing if applicable.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            p.product_id,
            p.name,
            p.price_brl,
            p.category_id,
            c.name AS category_name,
            p.description,
            p.stock_quantity,
            p.status,
            p.specs,
            promo.promotion_id,
            promo.discount_percent,
            promo.description AS promo_description,
            promo.is_active AS promo_is_active
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN promotions promo ON p.product_id = promo.product_id AND promo.is_active = 1
        WHERE 1=1
    """
    params: List[Any] = []

    if in_stock_only:
        sql += " AND p.stock_quantity > 0 AND p.status = 'active'"

    if query:
        # Search in product name or description
        tokens = query.strip().split()
        for token in tokens:
            sql += " AND (p.name LIKE ? OR p.description LIKE ? OR p.specs LIKE ?)"
            params.extend([f"%{token}%", f"%{token}%", f"%{token}%"])

    if category_name:
        sql += " AND (c.name LIKE ? OR c.description LIKE ?)"
        params.extend([f"%{category_name}%", f"%{category_name}%"])

    if min_price is not None:
        sql += " AND p.price_brl >= ?"
        params.append(min_price)

    if max_price is not None:
        sql += " AND p.price_brl <= ?"
        params.append(max_price)

    sql += " ORDER BY p.price_brl ASC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        price = float(r["price_brl"])
        promo_active = bool(r["promo_is_active"])
        discount_pct = float(r["discount_percent"]) if promo_active and r["discount_percent"] else 0.0

        if promo_active and discount_pct > 0:
            final_price = round(price * (1 - discount_pct / 100), 2)
            has_active_promo = True
        else:
            final_price = price
            has_active_promo = False

        payment_terms = calculate_payment_terms(final_price)

        results.append({
            "product_id": r["product_id"],
            "name": r["name"],
            "category": r["category_name"],
            "original_price": price,
            "original_price_formatted": format_currency_brl(price),
            "final_price": final_price,
            "final_price_formatted": format_currency_brl(final_price),
            "has_active_promotion": has_active_promo,
            "discount_percent": discount_pct if has_active_promo else 0,
            "promotion_description": r["promo_description"] if has_active_promo else None,
            "stock_quantity": r["stock_quantity"],
            "is_in_stock": r["stock_quantity"] > 0,
            "specs": r["specs"],
            "payment_terms": payment_terms,
        })

    conn.close()
    return results


def get_product_details(identifier: str) -> Optional[Dict[str, Any]]:
    """Fetch exact product details and promotion status by name or product ID."""
    conn = get_connection()
    cursor = conn.cursor()

    is_numeric = identifier.strip().isdigit()

    if is_numeric:
        sql = """
            SELECT p.*, c.name AS category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id = ?
        """
        cursor.execute(sql, (int(identifier),))
    else:
        # Match by name
        sql = """
            SELECT p.*, c.name AS category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.name LIKE ?
            ORDER BY
                CASE WHEN p.name = ? THEN 1
                     WHEN p.name LIKE ? THEN 2
                     ELSE 3 END,
                p.product_id ASC
            LIMIT 1
        """
        cursor.execute(sql, (f"%{identifier}%", identifier, f"{identifier}%"))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    product_id = row["product_id"]
    price = float(row["price_brl"])

    # Check for any promotions (both active and inactive)
    cursor.execute(
        "SELECT promotion_id, discount_percent, description, is_active FROM promotions WHERE product_id = ?",
        (product_id,),
    )
    promo_rows = cursor.fetchall()

    active_promo = None
    expired_promos = []

    for pr in promo_rows:
        promo_info = {
            "promotion_id": pr["promotion_id"],
            "discount_percent": float(pr["discount_percent"]),
            "description": pr["description"],
            "is_active": bool(pr["is_active"]),
        }
        if pr["is_active"] == 1:
            active_promo = promo_info
        else:
            expired_promos.append(promo_info)

    if active_promo:
        discount_pct = active_promo["discount_percent"]
        final_price = round(price * (1 - discount_pct / 100), 2)
        has_active_promo = True
    else:
        final_price = price
        has_active_promo = False

    payment_terms = calculate_payment_terms(final_price)

    result = {
        "product_id": row["product_id"],
        "name": row["name"],
        "category": row["category_name"],
        "description": row["description"],
        "specs": row["specs"],
        "original_price": price,
        "original_price_formatted": format_currency_brl(price),
        "final_price": final_price,
        "final_price_formatted": format_currency_brl(final_price),
        "has_active_promotion": has_active_promo,
        "active_promotion": active_promo,
        "expired_promotions": expired_promos,
        "stock_quantity": row["stock_quantity"],
        "is_in_stock": row["stock_quantity"] > 0,
        "status": row["status"],
        "payment_terms": payment_terms,
    }

    conn.close()
    return result


def get_order_status(
    tracking_code: Optional[str] = None,
    order_id: Optional[int] = None,
    customer_query: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve detailed order status, items, and delivery estimate."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            o.order_id,
            o.customer_id,
            o.order_date,
            o.status,
            o.total_brl,
            o.payment_method,
            o.tracking_code,
            o.estimated_delivery,
            o.notes,
            c.name AS customer_name,
            c.email AS customer_email,
            c.phone AS customer_phone,
            c.city AS customer_city
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE 1=1
    """
    params: List[Any] = []

    if tracking_code:
        sql += " AND UPPER(o.tracking_code) = UPPER(?)"
        params.append(tracking_code.strip())
    elif order_id is not None:
        sql += " AND o.order_id = ?"
        params.append(order_id)
    elif customer_query:
        sql += " AND (c.name LIKE ? OR c.email LIKE ? OR c.phone LIKE ?)"
        params.extend([f"%{customer_query}%", f"%{customer_query}%", f"%{customer_query}%"])
    else:
        conn.close()
        return None

    sql += " LIMIT 1"
    cursor.execute(sql, params)
    order_row = cursor.fetchone()

    if not order_row:
        conn.close()
        return None

    oid = order_row["order_id"]

    # Fetch ordered items
    item_sql = """
        SELECT
            oi.quantity,
            p.product_id,
            p.name AS product_name,
            p.price_brl
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
    """
    cursor.execute(item_sql, (oid,))
    item_rows = cursor.fetchall()

    items = []
    for item in item_rows:
        items.append({
            "product_id": item["product_id"],
            "name": item["product_name"],
            "quantity": item["quantity"],
            "unit_price": float(item["price_brl"]),
            "unit_price_formatted": format_currency_brl(float(item["price_brl"])),
        })

    status_translations = {
        "pending": "Aguardando pagamento",
        "confirmed": "Confirmado / Em preparação",
        "shipped": "Enviado / Em trânsito",
        "delivered": "Entregue",
        "cancelled": "Cancelado",
    }
    raw_status = order_row["status"]
    status_label = status_translations.get(raw_status, raw_status)

    result = {
        "order_id": order_row["order_id"],
        "order_date": order_row["order_date"],
        "status_raw": raw_status,
        "status_pt": status_label,
        "total_brl": float(order_row["total_brl"]),
        "total_brl_formatted": format_currency_brl(float(order_row["total_brl"])),
        "payment_method": order_row["payment_method"],
        "tracking_code": order_row["tracking_code"],
        "estimated_delivery": order_row["estimated_delivery"],
        "customer_name": order_row["customer_name"],
        "customer_city": order_row["customer_city"],
        "notes": order_row["notes"],
        "items": items,
    }

    conn.close()
    return result


def get_all_active_promotions() -> List[Dict[str, Any]]:
    """Retrieve all currently active promotions with associated product details."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            promo.promotion_id,
            promo.discount_percent,
            promo.description AS promo_description,
            p.product_id,
            p.name AS product_name,
            p.price_brl,
            c.name AS category_name
        FROM promotions promo
        JOIN products p ON promo.product_id = p.product_id
        JOIN categories c ON p.category_id = c.category_id
        WHERE promo.is_active = 1
        ORDER BY promo.discount_percent DESC
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    promos = []
    for r in rows:
        price = float(r["price_brl"])
        discount_pct = float(r["discount_percent"])
        discounted_price = round(price * (1 - discount_pct / 100), 2)
        promos.append({
            "promotion_id": r["promotion_id"],
            "product_id": r["product_id"],
            "product_name": r["product_name"],
            "category": r["category_name"],
            "original_price": price,
            "original_price_formatted": format_currency_brl(price),
            "discount_percent": discount_pct,
            "discounted_price": discounted_price,
            "discounted_price_formatted": format_currency_brl(discounted_price),
            "description": r["promo_description"],
        })

    conn.close()
    return promos
