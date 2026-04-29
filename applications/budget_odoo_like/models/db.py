# -*- coding: utf-8 -*-

if not request.env.web2py_runtime_gae:
    db = DAL('sqlite://storage.sqlite', pool_size=1, check_reserved=['all'])
else:
    db = DAL('google:datastore')
    session.connect(request, response, db=db)

response.generic_patterns = ['*'] if request.is_local else []

from gluon.tools import Auth, Crud, Service, PluginManager
from gluon import current

auth = Auth(db)
crud = Crud(db)
service = Service()
plugins = PluginManager()

auth.define_tables(username=False, signature=False)

# --- Master data ---
db.define_table(
    'res_partner',
    Field('name', 'string', required=True),
    Field('is_company', 'boolean', default=True),
    Field('vat', 'string', label='VAT/Tax ID'),
    Field('email', 'string'),
    Field('phone', 'string'),
    Field('street', 'string'),
    Field('city', 'string'),
    Field('zip', 'string'),
    Field('country', 'string'),
    Field('active', 'boolean', default=True),
    Field('create_date', 'datetime', default=request.now, writable=False),
    format='%(name)s'
)

db.define_table(
    'product_product',
    Field('name', 'string', required=True),
    Field('default_code', 'string', label='Internal Reference'),
    Field('type', 'string', requires=IS_IN_SET(['service', 'consumable', 'storable']), default='service'),
    Field('list_price', 'double', default=0.0),
    Field('standard_price', 'double', default=0.0),
    Field('active', 'boolean', default=True),
    Field('create_date', 'datetime', default=request.now, writable=False),
    format='%(name)s'
)

# --- Budget management ---
db.define_table(
    'budget_budget',
    Field('name', 'string', required=True),
    Field('fiscal_year', 'integer', required=True),
    Field('state', 'string', requires=IS_IN_SET(['draft', 'confirmed', 'closed']), default='draft'),
    Field('manager_id', 'reference auth_user', default=auth.user_id),
    Field('notes', 'text'),
    Field('create_date', 'datetime', default=request.now, writable=False),
    format='%(name)s'
)

db.define_table(
    'budget_line',
    Field('budget_id', 'reference budget_budget', required=True),
    Field('name', 'string', required=True),
    Field('partner_id', 'reference res_partner'),
    Field('planned_amount', 'double', default=0.0, required=True),
    Field('actual_amount', 'double', default=0.0, writable=False),
    Field('date_from', 'date'),
    Field('date_to', 'date'),
    Field('state', 'string', requires=IS_IN_SET(['open', 'done', 'cancelled']), default='open')
)

# --- Sales orders ---
db.define_table(
    'sale_order',
    Field('name', 'string', required=True, unique=True),
    Field('partner_id', 'reference res_partner', required=True),
    Field('date_order', 'datetime', default=request.now),
    Field('state', 'string', requires=IS_IN_SET(['draft', 'sent', 'sale', 'done', 'cancel']), default='draft'),
    Field('currency', 'string', default='EUR'),
    Field('amount_untaxed', 'double', default=0.0, writable=False),
    Field('amount_tax', 'double', default=0.0, writable=False),
    Field('amount_total', 'double', default=0.0, writable=False),
    Field('notes', 'text')
)

db.define_table(
    'sale_order_line',
    Field('order_id', 'reference sale_order', required=True),
    Field('product_id', 'reference product_product', required=True),
    Field('name', 'string'),
    Field('quantity', 'double', default=1.0, required=True),
    Field('price_unit', 'double', default=0.0, required=True),
    Field('discount', 'double', default=0.0),
    Field('tax_rate', 'double', default=22.0),
    Field('price_subtotal', 'double', default=0.0, writable=False),
    Field('price_tax', 'double', default=0.0, writable=False),
    Field('price_total', 'double', default=0.0, writable=False)
)

# --- Invoicing ---
db.define_table(
    'account_move',
    Field('name', 'string', required=True, unique=True),
    Field('move_type', 'string', requires=IS_IN_SET(['out_invoice', 'in_invoice', 'out_refund', 'in_refund']), default='out_invoice'),
    Field('partner_id', 'reference res_partner', required=True),
    Field('invoice_date', 'date', default=request.now.date()),
    Field('invoice_due_date', 'date'),
    Field('state', 'string', requires=IS_IN_SET(['draft', 'posted', 'paid', 'cancel']), default='draft'),
    Field('currency', 'string', default='EUR'),
    Field('amount_untaxed', 'double', default=0.0, writable=False),
    Field('amount_tax', 'double', default=0.0, writable=False),
    Field('amount_total', 'double', default=0.0, writable=False),
    Field('sale_order_id', 'reference sale_order')
)

db.define_table(
    'account_move_line',
    Field('move_id', 'reference account_move', required=True),
    Field('product_id', 'reference product_product'),
    Field('name', 'string', required=True),
    Field('quantity', 'double', default=1.0),
    Field('price_unit', 'double', default=0.0),
    Field('tax_rate', 'double', default=22.0),
    Field('price_subtotal', 'double', default=0.0, writable=False),
    Field('price_tax', 'double', default=0.0, writable=False),
    Field('price_total', 'double', default=0.0, writable=False)
)

db.define_table(
    'account_payment',
    Field('name', 'string', required=True, unique=True),
    Field('partner_id', 'reference res_partner', required=True),
    Field('payment_date', 'date', default=request.now.date()),
    Field('amount', 'double', required=True),
    Field('payment_type', 'string', requires=IS_IN_SET(['inbound', 'outbound']), default='inbound'),
    Field('state', 'string', requires=IS_IN_SET(['draft', 'posted', 'cancel']), default='draft'),
    Field('invoice_id', 'reference account_move'),
    Field('notes', 'text')
)


# --- Helpers for amount computation ---
def _line_amounts(quantity, unit_price, discount, tax_rate):
    subtotal = quantity * unit_price * (1.0 - (discount / 100.0))
    tax = subtotal * (tax_rate / 100.0)
    total = subtotal + tax
    return subtotal, tax, total


def _recompute_order(order_id):
    if not order_id:
        return
    lines = db(db.sale_order_line.order_id == order_id).select()
    untaxed = sum([l.price_subtotal or 0.0 for l in lines])
    tax = sum([l.price_tax or 0.0 for l in lines])
    db(db.sale_order.id == order_id).update(amount_untaxed=untaxed, amount_tax=tax, amount_total=untaxed + tax)


def _recompute_invoice(move_id):
    if not move_id:
        return
    lines = db(db.account_move_line.move_id == move_id).select()
    untaxed = sum([l.price_subtotal or 0.0 for l in lines])
    tax = sum([l.price_tax or 0.0 for l in lines])
    db(db.account_move.id == move_id).update(amount_untaxed=untaxed, amount_tax=tax, amount_total=untaxed + tax)


def sale_order_line_before_insert(fields):
    subtotal, tax, total = _line_amounts(fields.get('quantity', 0), fields.get('price_unit', 0), fields.get('discount', 0), fields.get('tax_rate', 0))
    fields['price_subtotal'] = subtotal
    fields['price_tax'] = tax
    fields['price_total'] = total


def sale_order_line_after_change(fields, line_id):
    line = db.sale_order_line[line_id]
    if line:
        subtotal, tax, total = _line_amounts(
            line.quantity or 0,
            line.price_unit or 0,
            line.discount or 0,
            line.tax_rate or 0
        )
        db(db.sale_order_line.id == line_id).update(
            price_subtotal=subtotal,
            price_tax=tax,
            price_total=total
        )
        _recompute_order(line.order_id)


def account_move_line_before_insert(fields):
    subtotal, tax, total = _line_amounts(fields.get('quantity', 0), fields.get('price_unit', 0), 0, fields.get('tax_rate', 0))
    fields['price_subtotal'] = subtotal
    fields['price_tax'] = tax
    fields['price_total'] = total


def account_move_line_after_change(fields, line_id):
    line = db.account_move_line[line_id]
    if line:
        subtotal, tax, total = _line_amounts(
            line.quantity or 0,
            line.price_unit or 0,
            0,
            line.tax_rate or 0
        )
        db(db.account_move_line.id == line_id).update(
            price_subtotal=subtotal,
            price_tax=tax,
            price_total=total
        )
        _recompute_invoice(line.move_id)


def sale_order_line_before_delete(deleted_set):
    order_ids = [r.order_id for r in deleted_set.select(db.sale_order_line.order_id)]
    current.request._deleted_order_ids = list(set([oid for oid in order_ids if oid]))


def sale_order_line_after_delete(deleted_set):
    for order_id in getattr(current.request, '_deleted_order_ids', []):
        _recompute_order(order_id)


def account_move_line_before_delete(deleted_set):
    move_ids = [r.move_id for r in deleted_set.select(db.account_move_line.move_id)]
    current.request._deleted_move_ids = list(set([mid for mid in move_ids if mid]))


def account_move_line_after_delete(deleted_set):
    for move_id in getattr(current.request, '_deleted_move_ids', []):
        _recompute_invoice(move_id)


db.sale_order_line._before_insert.append(sale_order_line_before_insert)
db.sale_order_line._after_insert.append(sale_order_line_after_change)
db.sale_order_line._after_update.append(sale_order_line_after_change)
db.sale_order_line._before_delete.append(sale_order_line_before_delete)
db.sale_order_line._after_delete.append(sale_order_line_after_delete)

db.account_move_line._before_insert.append(account_move_line_before_insert)
db.account_move_line._after_insert.append(account_move_line_after_change)
db.account_move_line._after_update.append(account_move_line_after_change)
db.account_move_line._before_delete.append(account_move_line_before_delete)
db.account_move_line._after_delete.append(account_move_line_after_delete)

for tname in db.tables:
    if tname not in ('auth_group', 'auth_membership', 'auth_permission', 'auth_event', 'auth_cas', 'auth_user'):
        db[tname].id.readable = True
        db[tname].id.writable = False
