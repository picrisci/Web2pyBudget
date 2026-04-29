# Web2pyBudget

Applicazione **web2py** per gestione di:
- budget
- ordini di vendita
- fatture e pagamenti

## Struttura creata

App: `applications/budget_odoo_like`

Schema ispirato a Odoo:
- `res_partner` (anagrafica clienti/fornitori)
- `product_product` (prodotti/servizi)
- `budget_budget` + `budget_line` (budget annuale e righe)
- `sale_order` + `sale_order_line` (ordini e righe)
- `account_move` + `account_move_line` (fatture e righe)
- `account_payment` (pagamenti)

## Avvio
1. Copia la cartella `applications/budget_odoo_like` dentro una installazione web2py.
2. Avvia web2py.
3. Apri l'app `budget_odoo_like`.

## Note
- I totali ordini/fatture vengono ricalcolati automaticamente tramite callback DAL sulle righe.
- Questa è una base pronta da estendere con workflow approvativi, permessi avanzati e report.
