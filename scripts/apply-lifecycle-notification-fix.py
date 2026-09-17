from pathlib import Path

ROOT=Path('.')
store=ROOT/'src/lib/supabase.ts'
admin=ROOT/'src/components/AdminDashboard.tsx'
orders=ROOT/'src/components/OrdersTab.tsx'
qris=ROOT/'src/components/QRISPaymentModal.tsx'
revision=ROOT/'src/components/RevisionModal.tsx'
app=ROOT/'src/App.tsx'

s=store.read_text()
marker='  static setFinalPrice(\n'
insert=r'''  static async orderAction(action: string, orderId: string, actorUserId: string, opts: { finalPrice?: number; status?: string; note?: string; fileName?: string; fileUrl?: string } = {}): Promise<{ success: boolean; message: string; order?: OrderItem }> {
    const supabase = getSupabase();
    if (!supabase) return { success: false, message: 'Database belum terhubung.' };
    const { data, error } = await supabase.rpc('custom_order_action', {
      p_actor_user_id: actorUserId,
      p_order_id: orderId,
      p_action: action,
      p_final_price: opts.finalPrice ?? null,
      p_status: opts.status ?? null,
      p_note: opts.note ?? null,
      p_file_name: opts.fileName ?? null,
      p_file_url: opts.fileUrl ?? null,
    });
    if (error) return { success: false, message: error.message || 'Aksi pesanan gagal.' };
    if (!data?.success) return { success: false, message: data?.message || 'Aksi pesanan gagal.' };
    if (data.order) {
      const updated = data.order as OrderItem;
      const cached = this.getOrders().filter(o => o.id !== updated.id);
      this.saveOrders([updated, ...cached]);
      return { success: true, message: data.message || 'Berhasil.', order: updated };
    }
    return { success: true, message: data.message || 'Berhasil.' };
  }

  static async getNotifications(userId: string): Promise<Array<{ id: string; title: string; message: string; type: string; order_id?: string; created_at: string }>> {
    const supabase = getSupabase();
    if (!supabase || !userId) return [];
    const { data, error } = await supabase.rpc('custom_get_notifications', { p_user_id: userId });
    if (error || !Array.isArray(data)) return [];
    return data as Array<{ id: string; title: string; message: string; type: string; order_id?: string; created_at: string }>;
  }

  static async markNotificationsRead(userId: string): Promise<void> {
    const supabase = getSupabase();
    if (!supabase || !userId) return;
    await supabase.rpc('custom_mark_notifications_read', { p_user_id: userId });
  }

'''
if marker not in s: raise SystemExit('store insertion marker missing')
s=s.replace(marker,insert+marker,1)
store.write_text(s)

# Admin actions become central Supabase mutations.
s=admin.read_text()
s=s.replace("  const handleSavePrice = (e: React.FormEvent) => {", "  const handleSavePrice = async (e: React.FormEvent) => {")
s=s.replace("    BeresinDataStore.setFinalPrice(\n      pricingOrder.id,\n      Number(inputFinalPrice),\n      pricingOrder.negotiation_requested ? (negotiationDecision as any) : undefined,\n      adminNote.trim() || undefined\n    );", "    const result = await BeresinDataStore.orderAction('set_price', pricingOrder.id, currentUser?.id || '', { finalPrice: Number(inputFinalPrice), note: adminNote.trim() || undefined });\n    if (!result.success) { window.alert(result.message); return; }")
s=s.replace("  const handleConfirmPayment = (orderId: string) => {", "  const handleConfirmPayment = async (orderId: string) => {")
s=s.replace("      BeresinDataStore.confirmPayment(orderId);\n      onRefreshData();", "      const result = await BeresinDataStore.orderAction('confirm_payment', orderId, currentUser?.id || '');\n      if (!result.success) { window.alert(result.message); return; }\n      onRefreshData();",1)
s=s.replace("  const handleStartWorking = (orderId: string) => {\n    BeresinDataStore.updateOrderStatus(orderId, 'DIKERJAKAN');\n    onRefreshData();\n  };", "  const handleStartWorking = async (orderId: string) => {\n    const result = await BeresinDataStore.orderAction('start_work', orderId, currentUser?.id || '', { status: 'DIKERJAKAN' });\n    if (!result.success) { window.alert(result.message); return; }\n    onRefreshData();\n  };")
s=s.replace("      BeresinDataStore.uploadWorkResult(\n        uploadResultOrder.id,\n        uploaded.fileName,\n        uploaded.fileUrl,\n        resultNotes.trim()\n      );", "      const result = await BeresinDataStore.orderAction('complete', uploadResultOrder.id, currentUser?.id || '', { fileName: uploaded.fileName, fileUrl: uploaded.fileUrl, note: resultNotes.trim() });\n      if (!result.success) throw new Error(result.message);")
admin.write_text(s)

# OrdersTab admin handlers are also centralized; student actions stay in the same UI but use RPCs.
s=orders.read_text()
s=s.replace("  const handleSavePrice = () => {", "  const handleSavePrice = async () => {")
s=s.replace("    BeresinDataStore.setFinalPriceAndVoucher(\n      priceModalOrder.id,\n      finalPriceInput,\n      negoStatus,\n      adminNoteInput || undefined\n    );", "    const result = await BeresinDataStore.orderAction('set_price', priceModalOrder.id, currentUser?.id || '', { finalPrice: finalPriceInput, note: adminNoteInput || undefined });\n    if (!result.success) { window.alert(result.message); return; }")
s=s.replace("  const handleConfirmQRIS = (orderId: string) => {\n    BeresinDataStore.confirmPayment(orderId);", "  const handleConfirmQRIS = async (orderId: string) => {\n    const result = await BeresinDataStore.orderAction('confirm_payment', orderId, currentUser?.id || '');\n    if (!result.success) { window.alert(result.message); return; }")
s=s.replace("  const handleStartWorking = (orderId: string) => {\n    BeresinDataStore.updateOrderStatus(orderId, 'DIKERJAKAN');", "  const handleStartWorking = async (orderId: string) => {\n    const result = await BeresinDataStore.orderAction('start_work', orderId, currentUser?.id || '', { status: 'DIKERJAKAN' });\n    if (!result.success) { window.alert(result.message); return; }")
s=s.replace("      BeresinDataStore.completeOrder(\n        uploadResultOrder.id,\n        finalName,\n        resultNotes || undefined,\n        uploadedUrl\n      );", "      const result = await BeresinDataStore.orderAction('complete', uploadResultOrder.id, currentUser?.id || '', { fileName: finalName, fileUrl: uploadedUrl, note: resultNotes || undefined });\n      if (!result.success) throw new Error(result.message);")
orders.write_text(s)

# Student payment proof goes to Supabase.
s=qris.read_text()
s=s.replace("      BeresinDataStore.submitPaymentProof(\n        order.id,\n        uploaded.fileName,\n        uploaded.fileUrl\n      );", "      const result = await BeresinDataStore.orderAction('payment_proof', order.id, order.student_id, { fileName: uploaded.fileName, fileUrl: uploaded.fileUrl });\n      if (!result.success) throw new Error(result.message);")
qris.write_text(s)

# Student revision goes to Supabase.
s=revision.read_text()
s=s.replace("  const handleSubmit = (e: React.FormEvent) => {", "  const handleSubmit = async (e: React.FormEvent) => {")
s=s.replace("    BeresinDataStore.requestRevision(order.id, revisionNotes.trim());", "    const result = await BeresinDataStore.orderAction('revision', order.id, order.student_id, { note: revisionNotes.trim() });\n    if (!result.success) { setErrorMsg(result.message); setIsSubmitting(false); return; }")
revision.write_text(s)

# Global notification toast + polling for every logged-in app instance.
s=app.read_text()
s=s.replace("  const [proofPreviewName, setProofPreviewName] = useState<string>('');", "  const [proofPreviewName, setProofPreviewName] = useState<string>('');\n  const [toastNotification, setToastNotification] = useState<{title: string; message: string} | null>(null);\n  const [lastNotificationId, setLastNotificationId] = useState<string | null>(null);")
needle="  useEffect(() => {\n    refreshData();\n  }, [currentUser, role]);"
replacement="""  useEffect(() => {\n    refreshData();\n  }, [currentUser, role]);\n\n  useEffect(() => {\n    if (!currentUser) return;\n    let active = true;\n    const poll = async () => {\n      const items = await BeresinDataStore.getNotifications(currentUser.id);\n      if (!active || items.length === 0) return;\n      const newest = items[0];\n      if (lastNotificationId && newest.id !== lastNotificationId) {\n        setToastNotification({ title: newest.title, message: newest.message });\n        window.setTimeout(() => setToastNotification(null), 5000);\n      }\n      if (!lastNotificationId) setLastNotificationId(newest.id);\n      else if (newest.id !== lastNotificationId) setLastNotificationId(newest.id);\n    };\n    void poll();\n    const timer = window.setInterval(() => void poll(), 4000);\n    return () => { active = false; window.clearInterval(timer); };\n  }, [currentUser?.id, lastNotificationId]);"""
if needle not in s: raise SystemExit('App polling marker missing')
s=s.replace(needle,replacement,1)
# Render toast immediately before closing main app return container marker.
render_marker="    <div className=\"min-h-screen"
toast="""    {toastNotification && (\n      <div className=\"fixed top-4 right-4 z-[100] w-[min(92vw,380px)] rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl animate-in slide-in-from-top-3 duration-200\">\n        <div className=\"flex items-start gap-3\">\n          <div className=\"mt-0.5 h-9 w-9 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-lg\">✓</div>\n          <div className=\"min-w-0 flex-1\"><p className=\"font-black text-slate-900 text-sm\">{toastNotification.title}</p><p className=\"text-xs text-slate-600 mt-1\">{toastNotification.message}</p></div>\n          <button onClick={() => setToastNotification(null)} className=\"text-slate-400 hover:text-slate-700\">×</button>\n        </div>\n      </div>\n    )}\n"""
if render_marker not in s: raise SystemExit('App render marker missing')
s=s.replace(render_marker,toast+render_marker,1)
app.write_text(s)
