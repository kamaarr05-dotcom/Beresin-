from pathlib import Path

ROOT = Path('.')

# Keep the checked-in ZIP as the source bundle, but apply these deterministic edits
# after extraction so the deployed source cannot regress to the old localStorage flow.
order_modal = ROOT / 'src/components/OrderModal.tsx'
app = ROOT / 'src/App.tsx'
store = ROOT / 'src/lib/supabase.ts'

text = order_modal.read_text()
text = text.replace(
    "  onOrderCreated: () => void;",
    "  onOrderCreated: (order: import('../types').OrderItem) => void;",
)
text = text.replace("      if (order) onOrderCreated(order);", "      if (result.order) onOrderCreated(result.order);")
text = text.replace("      onOrderCreated();", "      if (result.order) onOrderCreated(result.order);")
order_modal.write_text(text)

text = app.read_text()
old = """        onOrderCreated={() => {\n          refreshData();\n          setMobileTab('pesanan');\n          setDesktopView('student-orders');\n        }}"""
new = """        onOrderCreated={(createdOrder) => {\n          void refreshData();\n          setMobileTab('pesanan');\n          setDesktopView('student-orders');\n          if (createdOrder.status === 'MENUNGGU_PEMBAYARAN' && createdOrder.amount_to_pay > 0) {\n            setPaymentOrder(createdOrder);\n            setIsPaymentModalOpen(true);\n          }\n        }}"""
if old not in text:
    raise SystemExit('App.tsx order-created handler was not found')
text = text.replace(old, new)
app.write_text(text)

# Make the local fallback consistent with the central RPC semantics.
text = store.read_text()
old = """      // If no negotiation requested, base price is candidate price; Admin will verify and set final price\n      final_price: orderData.negotiationRequested ? null : orderData.service.base_price,\n      voucher_deduction: 0,\n      amount_to_pay: 0,\n      status: 'MENUNGGU_HARGA',"""
new = """      final_price: orderData.negotiationRequested ? null : orderData.service.base_price,\n      voucher_deduction: orderData.negotiationRequested ? 0 : Math.min(orderData.service.base_price, this.getUserById(orderData.student.id)?.voucher_balance || 0),\n      amount_to_pay: orderData.negotiationRequested ? 0 : Math.max(0, orderData.service.base_price - Math.min(orderData.service.base_price, this.getUserById(orderData.student.id)?.voucher_balance || 0)),\n      status: orderData.negotiationRequested\n        ? 'MENUNGGU_HARGA'\n        : (Math.max(0, orderData.service.base_price - Math.min(orderData.service.base_price, this.getUserById(orderData.student.id)?.voucher_balance || 0)) === 0 ? 'ANTRIAN' : 'MENUNGGU_PEMBAYARAN'),"""
if old in text:
    text = text.replace(old, new)
store.write_text(text)
