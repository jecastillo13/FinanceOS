import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../modules/record_form_page.dart';

class RecurringPage extends StatefulWidget {
  const RecurringPage({super.key});
  @override
  State<RecurringPage> createState() => _RecurringPageState();
}

class _RecurringPageState extends State<RecurringPage> {
  final _api = ApiClient();
  late Future<List<dynamic>> _items = _api.recurrentes();
  List<dynamic> _accounts = [];
  @override
  void initState() {
    super.initState();
    _api.cuentas().then((v) {
      if (mounted) setState(() => _accounts = v);
    });
  }

  void _reload() => setState(() => _items = _api.recurrentes());
  String money(Object? value) =>
      NumberFormat.currency(locale: 'es_CO', symbol: r'$ ', decimalDigits: 0)
          .format((value as num?) ?? 0);
  Future<void> _form([Map<String, dynamic>? item]) async {
    final changed = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
            builder: (_) => RecordFormPage(
                resource: 'gastos-recurrentes',
                title: 'Pago recurrente',
                initial: item)));
    if (changed == true) _reload();
  }

  Future<void> _pay(Map<String, dynamic> item) async {
    if (_accounts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Primero crea una cuenta.')));
      return;
    }
    var account = _accounts.first['id'] as int;
    final ok = await showDialog<bool>(
        context: context,
        builder: (context) => StatefulBuilder(
            builder: (context, setDialog) => AlertDialog(
                  title: Text('Pagar ${item['nombre']}'),
                  content: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                            'Se creará un gasto por ${money(item['valor'])} y se descontará la cuenta elegida.',
                            style: const TextStyle(color: FinanceColors.muted)),
                        const SizedBox(height: 14),
                        DropdownButtonFormField<int>(
                            initialValue: account,
                            decoration: const InputDecoration(
                                labelText: 'Cuenta que pagará'),
                            items: _accounts
                                .map((a) => DropdownMenuItem<int>(
                                    value: a['id'] as int,
                                    child: Text(
                                        '${a['nombre']} (${a['moneda']})')))
                                .toList(),
                            onChanged: (v) => setDialog(() => account = v!)),
                      ]),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Registrar pago'))
                  ],
                )));
    if (ok != true) return;
    try {
      await _api.pagarRecurrente(item['id'] as int, account);
      _reload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Pagos recurrentes')),
        floatingActionButton: FloatingActionButton.extended(
            onPressed: () => _form(),
            icon: const Icon(Icons.add),
            label: const Text('Crear pago')),
        body: FinanceAurora(
            child: SafeArea(
                child: FutureBuilder<List<dynamic>>(
                    future: _items,
                    builder: (context, snapshot) {
                      if (snapshot.connectionState != ConnectionState.done) {
                        return const Center(child: CircularProgressIndicator());
                      }
                      return RefreshIndicator(
                          onRefresh: () async => _reload(),
                          child: ListView(
                              padding:
                                  const EdgeInsets.fromLTRB(18, 12, 18, 110),
                              children: [
                                const FinanceSurface(
                                    child: Text(
                                        'Al registrar un pago se descuenta la cuenta y se crea el gasto; no debes registrarlo nuevamente.',
                                        style: TextStyle(
                                            color: FinanceColors.muted,
                                            height: 1.45))),
                                const SizedBox(height: 14),
                                ...(snapshot.data ?? []).map((raw) =>
                                    _item(raw as Map<String, dynamic>)),
                              ]));
                    }))),
      );
  Widget _item(Map<String, dynamic> item) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: FinanceSurface(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.event_repeat_rounded, color: FinanceColors.cyan),
          const SizedBox(width: 10),
          Expanded(
              child: Text('${item['nombre']}',
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w900))),
          IconButton(
              onPressed: () => _form(item),
              icon: const Icon(Icons.edit_outlined)),
          IconButton(
              onPressed: () async {
                await _api.eliminar('gastos-recurrentes', item['id']);
                _reload();
              },
              icon: const Icon(Icons.delete_outline))
        ]),
        Text(money(item['valor']),
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
        Text('${item['frecuencia']} · Próximo: ${item['proxima_fecha_pago']}',
            style: const TextStyle(color: FinanceColors.muted)),
        const SizedBox(height: 14),
        FilledButton.icon(
            onPressed: () => _pay(item),
            icon: const Icon(Icons.account_balance_wallet_outlined),
            label: const Text('Pagar desde una cuenta')),
      ])));
}
