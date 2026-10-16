"""Esquema inicial do Cali Burger.

Cria todas as tabelas e as categorias do cardápio (dado de referência,
sem tela de gestão — igual ao sistema original).

Revision ID: 0c37c2b59602
Revises:
Create Date: 2026-10-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0c37c2b59602"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES_IN_DROP_ORDER = (
    "recipe_items",
    "payments",
    "order_status_events",
    "order_items",
    "order_consumptions",
    "sessions",
    "orders",
    "menu_items",
    "customer_addresses",
    "users",
    "login_attempts",
    "ingredients",
    "categories",
)


def upgrade() -> None:
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_categories')),
    sa.UniqueConstraint('name', name=op.f('uq_categories_name'))
    )
    op.create_table('ingredients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.CheckConstraint('quantity >= 0', name=op.f('ck_ingredients_quantity_non_negative')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ingredients')),
    sa.UniqueConstraint('name', name=op.f('uq_ingredients_name'))
    )
    op.create_table('login_attempts',
    sa.Column('key_hash', sa.CHAR(length=64), nullable=False),
    sa.Column('failures', sa.Integer(), nullable=False),
    sa.Column('window_started_at', sa.DateTime(), nullable=False),
    sa.Column('locked_until', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('key_hash', name=op.f('pk_login_attempts'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('role', sa.Enum('customer', 'manager', 'cook', name='user_role'), nullable=False),
    sa.Column('account_type', sa.String(length=8), sa.Computed("(case when `role` = 'customer' then 'customer' else 'staff' end)", persisted=True), nullable=False),
    sa.Column('username', sa.String(length=30), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('cpf', sa.CHAR(length=11), nullable=False),
    sa.Column('birth_date', sa.Date(), nullable=False),
    sa.Column('sex', sa.Enum('male', 'female', 'other', name='user_sex'), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('password_changed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('cpf', 'account_type', name=op.f('uq_users_cpf_account_type')),
    sa.UniqueConstraint('username', name=op.f('uq_users_username'))
    )
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_table('customer_addresses',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.String(length=255), nullable=False),
    sa.Column('city', sa.String(length=255), nullable=False),
    sa.Column('district', sa.String(length=255), nullable=False),
    sa.Column('street', sa.String(length=255), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_customer_addresses_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_customer_addresses'))
    )
    op.create_table('menu_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('image_path', sa.String(length=255), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.CheckConstraint('price > 0', name=op.f('ck_menu_items_price_positive')),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name=op.f('fk_menu_items_category_id_categories'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_menu_items'))
    )
    op.create_index(op.f('ix_menu_items_category_id'), 'menu_items', ['category_id'], unique=False)
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('customer_name', sa.String(length=100), nullable=False),
    sa.Column('delivery_address', sa.String(length=1100), nullable=True),
    sa.Column('status', sa.Enum('awaiting_acceptance', 'in_preparation', 'out_for_delivery', 'completed', 'cancelled', 'rejected', name='order_status'), nullable=False),
    sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('idempotency_key', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
    sa.CheckConstraint('total > 0', name=op.f('ck_orders_total_positive')),
    sa.ForeignKeyConstraint(['customer_id'], ['users.id'], name=op.f('fk_orders_customer_id_users'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_orders')),
    sa.UniqueConstraint('customer_id', 'idempotency_key', name=op.f('uq_orders_customer_id_idempotency_key'))
    )
    op.create_index('ix_orders_created_at', 'orders', ['created_at'], unique=False)
    op.create_index('ix_orders_customer_id_created_at', 'orders', ['customer_id', 'created_at'], unique=False)
    op.create_index('ix_orders_status_created_at', 'orders', ['status', 'created_at'], unique=False)
    op.create_table('sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.CHAR(length=64), nullable=False),
    sa.Column('csrf_hash', sa.CHAR(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sessions')),
    sa.UniqueConstraint('token_hash', name=op.f('uq_sessions_token_hash'))
    )
    op.create_index(op.f('ix_sessions_expires_at'), 'sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_table('order_consumptions',
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('ingredient_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_order_consumptions_quantity_positive')),
    sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], name=op.f('fk_order_consumptions_ingredient_id_ingredients'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_consumptions_order_id_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('order_id', 'ingredient_id', name=op.f('pk_order_consumptions'))
    )
    op.create_index(op.f('ix_order_consumptions_ingredient_id'), 'order_consumptions', ['ingredient_id'], unique=False)
    op.create_table('order_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('menu_item_id', sa.Integer(), nullable=True),
    sa.Column('product_name', sa.String(length=100), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('notes', sa.String(length=255), nullable=True),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_order_items_quantity_positive')),
    sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], name=op.f('fk_order_items_menu_item_id_menu_items'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_items_order_id_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_order_items'))
    )
    op.create_index(op.f('ix_order_items_menu_item_id'), 'order_items', ['menu_item_id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_table('order_status_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('from_status', sa.Enum('awaiting_acceptance', 'in_preparation', 'out_for_delivery', 'completed', 'cancelled', 'rejected', name='order_status'), nullable=True),
    sa.Column('to_status', sa.Enum('awaiting_acceptance', 'in_preparation', 'out_for_delivery', 'completed', 'cancelled', 'rejected', name='order_status'), nullable=False),
    sa.Column('actor_id', sa.Integer(), nullable=True),
    sa.Column('actor_name', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_order_status_events_actor_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_order_status_events_order_id_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_order_status_events'))
    )
    op.create_index(op.f('ix_order_status_events_actor_id'), 'order_status_events', ['actor_id'], unique=False)
    op.create_index(op.f('ix_order_status_events_order_id'), 'order_status_events', ['order_id'], unique=False)
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('method', sa.Enum('pix', name='payment_method'), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('paid_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], name=op.f('fk_payments_order_id_orders'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_payments')),
    sa.UniqueConstraint('order_id', name=op.f('uq_payments_order_id'))
    )
    op.create_table('recipe_items',
    sa.Column('menu_item_id', sa.Integer(), nullable=False),
    sa.Column('ingredient_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.CheckConstraint('quantity > 0', name=op.f('ck_recipe_items_quantity_positive')),
    sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], name=op.f('fk_recipe_items_ingredient_id_ingredients'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], name=op.f('fk_recipe_items_menu_item_id_menu_items'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('menu_item_id', 'ingredient_id', name=op.f('pk_recipe_items'))
    )
    op.create_index(op.f('ix_recipe_items_ingredient_id'), 'recipe_items', ['ingredient_id'], unique=False)

    categories = sa.table(
        "categories",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("position", sa.Integer),
    )
    op.bulk_insert(
        categories,
        [
            {"id": 1, "name": "Lanches", "position": 1},
            {"id": 2, "name": "Acompanhamentos", "position": 2},
            {"id": 3, "name": "Bebidas", "position": 3},
        ],
    )


def downgrade() -> None:
    for table in TABLES_IN_DROP_ORDER:
        op.drop_table(table)
