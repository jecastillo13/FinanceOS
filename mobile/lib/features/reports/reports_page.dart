import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';
import '../../core/api_client.dart';
import '../../core/design_system.dart';

class ReportsPage extends StatefulWidget {
  const ReportsPage({super.key});
  @override
  State<ReportsPage> createState() => _ReportsPageState();
}

class _ReportsPageState extends State<ReportsPage> {
  final _api = ApiClient();
  int month = DateTime.now().month, year = DateTime.now().year;
  late Future<Map<String, dynamic>> report = load();
  bool exporting = false;
  Future<Map<String, dynamic>> load() => _api.reporte(anio: year, mes: month);
  void refresh() => setState(() => report = load());
  Future<void> export(String format) async {
    setState(() => exporting = true);
    try {
      final bytes =
          await _api.descargarReporte(anio: year, mes: month, formato: format);
      final mime = format == 'pdf'
          ? 'application/pdf'
          : format == 'xlsx'
              ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
              : 'text/csv';
      await Share.shareXFiles([
        XFile.fromData(bytes,
            name:
                'financeos_${year}_${month.toString().padLeft(2, '0')}.$format',
            mimeType: mime)
      ], text: 'Reporte FinanceOS');
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      if (mounted) setState(() => exporting = false);
    }
  }

  String money(Object? value) =>
      NumberFormat.currency(locale: 'es_CO', symbol: r'$ ', decimalDigits: 0)
          .format((value as num?) ?? 0);
  Widget metric(String name, Object? value, Color color) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: FinanceSurface(
          accent: color,
          child: ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(name),
              trailing: Text(money(value),
                  style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: color)))));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reportes')),
      body: FinanceAurora(
          child: SafeArea(
              child: FutureBuilder<Map<String, dynamic>>(
        future: report,
        builder: (context, snapshot) {
          final data = snapshot.data;
          return ListView(padding: const EdgeInsets.all(18), children: [
            FinanceSurface(
                child: Row(children: [
              Expanded(
                  child: DropdownButtonFormField<int>(
                      initialValue: month,
                      decoration: const InputDecoration(labelText: 'Mes'),
                      items: List.generate(
                          12,
                          (i) => DropdownMenuItem(
                              value: i + 1, child: Text('${i + 1}'))),
                      onChanged: (v) {
                        month = v!;
                        refresh();
                      })),
              const SizedBox(width: 12),
              Expanded(
                  child: DropdownButtonFormField<int>(
                      initialValue: year,
                      decoration: const InputDecoration(labelText: 'Año'),
                      items: [year - 1, year, year + 1]
                          .map((v) =>
                              DropdownMenuItem(value: v, child: Text('$v')))
                          .toList(),
                      onChanged: (v) {
                        year = v!;
                        refresh();
                      })),
            ])),
            const SizedBox(height: 16),
            FinanceSurface(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                  const Text('Exportar y compartir',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 6),
                  const Text('Genera el mismo archivo que en la web.',
                      style: TextStyle(color: FinanceColors.muted)),
                  const SizedBox(height: 12),
                  Wrap(
                      spacing: 8,
                      children: ['pdf', 'xlsx', 'csv']
                          .map((format) => OutlinedButton(
                              onPressed:
                                  exporting ? null : () => export(format),
                              child: Text(format.toUpperCase())))
                          .toList()),
                ])),
            const SizedBox(height: 16),
            if (snapshot.connectionState != ConnectionState.done)
              const Center(child: CircularProgressIndicator())
            else if (snapshot.hasError)
              FinanceSurface(child: Text('${snapshot.error}'))
            else ...[
              metric('Ingresos', data?['ingresos_cop'], FinanceColors.success),
              metric('Gastos', data?['gastos_cop'], FinanceColors.danger),
              metric('Balance', data?['balance_cop'], FinanceColors.cyan),
              FinanceSurface(
                  child: Text(
                      '${data?['movimientos'] ?? 0} movimientos analizados',
                      style: const TextStyle(fontWeight: FontWeight.w700))),
            ],
          ]);
        },
      ))),
    );
  }
}
