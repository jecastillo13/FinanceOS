import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/api_client.dart';
import '../../core/design_system.dart';

class MobileCurrenciesPage extends StatefulWidget {
  const MobileCurrenciesPage({super.key});
  @override
  State<MobileCurrenciesPage> createState() => _MobileCurrenciesPageState();
}

class _MobileCurrenciesPageState extends State<MobileCurrenciesPage> {
  final _api = ApiClient();
  final _value = TextEditingController(text: '100');
  late Future<List<dynamic>> _rates = _api.tasas();
  String from = 'USD', to = 'COP';
  Map<String, dynamic>? result;
  bool busy = false;

  void reload() => setState(() => _rates = _api.tasas());
  Future<void> update() async {
    setState(() => busy = true);
    try {
      await _api.actualizarTasas();
      reload();
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> convert() async {
    setState(() => busy = true);
    try {
      result = await _api.convertir(
          double.parse(_value.text.replaceAll(',', '.')), from, to);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void dispose() {
    _value.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Monedas y tasas')),
        body: FinanceAurora(
            child: SafeArea(
                child: FutureBuilder<List<dynamic>>(
          future: _rates,
          builder: (context, snapshot) {
            final rates = snapshot.data ?? [];
            final currencies = <String>{
              'COP',
              'USD',
              'EUR',
              ...rates.expand(
                  (r) => ['${r['moneda_origen']}', '${r['moneda_destino']}'])
            }.toList();
            Widget selector(
                    String label, String value, ValueChanged<String> change) =>
                DropdownButtonFormField<String>(
                  initialValue: value,
                  decoration: InputDecoration(labelText: label),
                  items: currencies
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) {
                    if (v != null) change(v);
                  },
                );
            return ListView(padding: const EdgeInsets.all(18), children: [
              FinanceSurface(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                    Text('Convertir moneda',
                        style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 12),
                    TextField(
                        controller: _value,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Valor')),
                    const SizedBox(height: 10),
                    Row(children: [
                      Expanded(
                          child: selector(
                              'Origen', from, (v) => setState(() => from = v))),
                      const SizedBox(width: 10),
                      Expanded(
                          child: selector(
                              'Destino', to, (v) => setState(() => to = v))),
                    ]),
                    const SizedBox(height: 12),
                    FilledButton.icon(
                        onPressed: busy ? null : convert,
                        icon: const Icon(Icons.currency_exchange),
                        label: const Text('Convertir')),
                    if (result != null) ...[
                      const SizedBox(height: 14),
                      Text(
                          '${NumberFormat.decimalPattern('es_CO').format(result!['valor_convertido'])} ${result!['destino']}',
                          style: const TextStyle(
                              fontSize: 25, fontWeight: FontWeight.w900)),
                    ],
                  ])),
              const SizedBox(height: 14),
              FilledButton.tonalIcon(
                  onPressed: busy ? null : update,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Actualizar tasas')),
              const SizedBox(height: 14),
              ...rates.take(30).map((r) => FinanceSurface(
                  child: ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(
                          '${r['moneda_origen']} → ${r['moneda_destino']}'),
                      trailing: Text('${r['tasa']}',
                          style:
                              const TextStyle(fontWeight: FontWeight.w900))))),
            ]);
          },
        ))),
      );
}
