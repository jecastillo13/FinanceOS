import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../detections/detections_page.dart';
import '../modules/record_form_page.dart';

class MobileCardsPage extends StatefulWidget {
  const MobileCardsPage({super.key});
  @override
  State<MobileCardsPage> createState() => _MobileCardsPageState();
}

class _MobileCardsPageState extends State<MobileCardsPage> {
  final _api = ApiClient();
  late Future<List<dynamic>> _cards = _api.tarjetas();
  List<dynamic> _accounts = [];
  @override
  void initState() {
    super.initState();
    _api.cuentas().then((v) {
      if (mounted) setState(() => _accounts = v);
    });
  }

  void _reload() => setState(() => _cards = _api.tarjetas());
  String money(Object? value, String currency) => NumberFormat.currency(
          locale: 'es_CO',
          symbol: '$currency ',
          decimalDigits: currency == 'COP' ? 0 : 2)
      .format((value as num?) ?? 0);
  Future<void> _create() async {
    final changed = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
            builder: (_) =>
                const RecordFormPage(resource: 'tarjetas', title: 'Tarjeta')));
    if (changed == true) _reload();
  }

  Future<void> _pay(Map<String, dynamic> card) async {
    final options = _accounts
        .where((a) =>
            a['moneda'] == card['moneda'] && a['id'] != card['cuenta_id'])
        .toList();
    if (options.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No hay una cuenta compatible para pagar.')));
      return;
    }
    var account = options.first['id'] as int;
    final value =
        TextEditingController(text: '${((card['saldo'] as num?) ?? 0).abs()}');
    final ok = await showDialog<bool>(
        context: context,
        builder: (context) => StatefulBuilder(
            builder: (context, setDialog) => AlertDialog(
                  title: Text('Pagar ${card['nombre']}'),
                  content: Column(mainAxisSize: MainAxisSize.min, children: [
                    const Text(
                        'Reduce la cuenta bancaria y también la deuda. No crea un gasto duplicado.',
                        style: TextStyle(color: FinanceColors.muted)),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<int>(
                        initialValue: account,
                        decoration:
                            const InputDecoration(labelText: 'Pagar desde'),
                        items: options
                            .map((a) => DropdownMenuItem<int>(
                                value: a['id'] as int,
                                child: Text('${a['nombre']}')))
                            .toList(),
                        onChanged: (v) => setDialog(() => account = v!)),
                    const SizedBox(height: 10),
                    TextField(
                        controller: value,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Valor')),
                  ]),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Confirmar pago'))
                  ],
                )));
    if (ok == true) {
      try {
        await _api.pagarTarjeta(
            card['id'], account, double.parse(value.text.replaceAll(',', '.')));
        _reload();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text('$e')));
        }
      }
    }
    value.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Tarjetas y compras')),
        floatingActionButton: FloatingActionButton.extended(
            onPressed: _create,
            icon: const Icon(Icons.add),
            label: const Text('Nueva tarjeta')),
        body: FinanceAurora(
            child: SafeArea(
                child: FutureBuilder<List<dynamic>>(
                    future: _cards,
                    builder: (context, snapshot) {
                      if (snapshot.connectionState != ConnectionState.done) {
                        return const Center(child: CircularProgressIndicator());
                      }
                      final cards = snapshot.data ?? [];
                      return RefreshIndicator(
                          onRefresh: () async => _reload(),
                          child: ListView(
                              padding:
                                  const EdgeInsets.fromLTRB(18, 12, 18, 110),
                              children: [
                                FinanceSurface(
                                    child: ListTile(
                                        contentPadding: EdgeInsets.zero,
                                        leading: const Icon(
                                            Icons.notifications_active_rounded,
                                            color: FinanceColors.cyan),
                                        title:
                                            const Text('Compras por confirmar'),
                                        subtitle: const Text(
                                            'Revisa avisos bancarios antes de registrarlos'),
                                        trailing:
                                            const Icon(Icons.chevron_right),
                                        onTap: () => Navigator.push(
                                            context,
                                            MaterialPageRoute(
                                                builder: (_) =>
                                                    const DetectionsPage())))),
                                const SizedBox(height: 14),
                                ...cards.map((raw) =>
                                    _card(raw as Map<String, dynamic>)),
                              ]));
                    }))),
      );
  Widget _card(Map<String, dynamic> card) {
    final debt =
        card['tipo'] == 'Credito' && ((card['saldo'] as num?) ?? 0) < 0;
    return Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: FinanceSurface(
            accent: FinanceColors.primary,
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.credit_card_rounded,
                    color: FinanceColors.cyan),
                const Spacer(),
                Text('${card['tipo']} · ${card['moneda']}',
                    style: const TextStyle(color: FinanceColors.muted)),
                IconButton(
                    onPressed: () async {
                      await _api.eliminar('tarjetas', card['id']);
                      _reload();
                    },
                    icon: const Icon(Icons.delete_outline))
              ]),
              Text('${card['nombre']}',
                  style: const TextStyle(
                      fontSize: 21, fontWeight: FontWeight.w900)),
              Text('${card['banco']} · •••• ${card['ultimos_cuatro']}',
                  style: const TextStyle(color: FinanceColors.muted)),
              const SizedBox(height: 13),
              Text(
                  debt
                      ? 'Deuda: ${money(((card['saldo'] as num?) ?? 0).abs(), '${card['moneda']}')}'
                      : 'Vinculada a ${card['cuenta']}',
                  style: const TextStyle(fontWeight: FontWeight.w800)),
              if (debt) ...[
                const SizedBox(height: 12),
                FilledButton.icon(
                    onPressed: () => _pay(card),
                    icon: const Icon(Icons.payments_outlined),
                    label: const Text('Pagar tarjeta'))
              ],
            ])));
  }
}
