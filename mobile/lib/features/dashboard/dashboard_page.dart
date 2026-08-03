import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final _api = ApiClient();
  late Future<_DashboardData> _data = _load();

  Future<_DashboardData> _load() async => _DashboardData(
        await _api.resumenDashboard(),
        await _api.cuentas(),
      );

  String _money(Object? value) => NumberFormat.currency(locale: 'es_CO', symbol: 'COP ', decimalDigits: 0)
      .format((value as num?) ?? 0);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('FinanceOS'), actions: [IconButton(onPressed: () => setState(() => _data = _load()), icon: const Icon(Icons.refresh))]),
      body: FutureBuilder<_DashboardData>(
        future: _data,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snapshot.hasError) return _ErrorState(error: snapshot.error.toString(), onRetry: () => setState(() => _data = _load()));
          final data = snapshot.data!;
          return RefreshIndicator(
            onRefresh: () async => setState(() => _data = _load()),
            child: ListView(padding: const EdgeInsets.all(20), children: [
              const Text('Centro financiero', style: TextStyle(fontSize: 27, fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              const Text('Tu panorama financiero, siempre contigo.'),
              const SizedBox(height: 20),
              _MetricCard(label: 'Patrimonio', value: _money(data.resumen['patrimonio']), icon: Icons.account_balance_wallet_rounded),
              const SizedBox(height: 12),
              Row(children: [Expanded(child: _MetricCard(label: 'Ingresos', value: _money(data.resumen['ingresos']), icon: Icons.south_west_rounded)), const SizedBox(width: 12), Expanded(child: _MetricCard(label: 'Gastos', value: _money(data.resumen['gastos']), icon: Icons.north_east_rounded))]),
              const SizedBox(height: 28),
              const Text('Mis cuentas', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              ...data.cuentas.map((cuenta) => Card(child: ListTile(leading: const CircleAvatar(child: Icon(Icons.account_balance_rounded)), title: Text(cuenta['nombre'] as String), subtitle: Text(cuenta['tipo'] as String), trailing: Text('${cuenta['moneda']} ${cuenta['saldo']}', style: const TextStyle(fontWeight: FontWeight.bold))))),
            ]),
          );
        },
      ),
    );
  }
}

class _DashboardData { const _DashboardData(this.resumen, this.cuentas); final Map<String, dynamic> resumen; final List<dynamic> cuentas; }
class _MetricCard extends StatelessWidget { const _MetricCard({required this.label, required this.value, required this.icon}); final String label, value; final IconData icon; @override Widget build(BuildContext context) => Container(padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: Theme.of(context).colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(22)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon), const SizedBox(height: 14), Text(label), const SizedBox(height: 4), Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700))])); }
class _ErrorState extends StatelessWidget { const _ErrorState({required this.error, required this.onRetry}); final String error; final VoidCallback onRetry; @override Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(30), child: Column(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.cloud_off_rounded, size: 56), const SizedBox(height: 16), const Text('No pudimos conectar FinanceOS móvil con la API.', textAlign: TextAlign.center), const SizedBox(height: 8), Text(error, textAlign: TextAlign.center), const SizedBox(height: 18), FilledButton(onPressed: onRetry, child: const Text('Reintentar'))]))); }
