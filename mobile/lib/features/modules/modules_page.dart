import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../detections/detections_page.dart';
import 'collection_page.dart';

class ModulesPage extends StatelessWidget {
  const ModulesPage({super.key});

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final modules = <_Module>[
      _Module('Cuentas', Icons.account_balance_wallet_rounded,
          (a) => a.cuentas(), 'cuentas'),
      _Module('Tarjetas', Icons.credit_card_rounded, (a) => a.tarjetas(),
          'tarjetas'),
      _Module('Categorías', Icons.sell_rounded, (a) => a.categorias(),
          'categorias'),
      _Module('Recurrentes', Icons.event_repeat_rounded, (a) => a.recurrentes(),
          'gastos-recurrentes'),
      _Module('Transferencias', Icons.swap_horiz_rounded,
          (a) => a.transferencias(), 'transferencias'),
      _Module(
          'Presupuestos',
          Icons.donut_large_rounded,
          (a) => a.presupuestos(anio: now.year, mes: now.month),
          'presupuestos'),
      _Module('Metas', Icons.track_changes_rounded, (a) => a.metas(), 'metas'),
      _Module(
          'Inversiones',
          Icons.trending_up_rounded,
          (a) async =>
              ((await a.inversiones())['posiciones'] as List<dynamic>? ?? []),
          'inversiones'),
      _Module('Monedas', Icons.currency_exchange_rounded, (a) => a.tasas()),
    ];
    return Scaffold(
        body: FinanceAurora(
            child: SafeArea(
                child: ListView(
                    padding: const EdgeInsets.fromLTRB(18, 18, 18, 110),
                    children: [
          const Text('FinanceOS',
              style: TextStyle(
                  color: FinanceColors.cyan,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.5)),
          const SizedBox(height: 6),
          Text('Todos tus módulos',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
              'La información se sincroniza con la misma API utilizada por la web.',
              style: TextStyle(color: FinanceColors.muted)),
          const SizedBox(height: 22),
          GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: 1.18),
              itemCount: modules.length,
              itemBuilder: (context, index) {
                final module = modules[index];
                return InkWell(
                    borderRadius: BorderRadius.circular(24),
                    onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => CollectionPage(
                                title: module.name,
                                icon: module.icon,
                                loader: module.loader,
                                deleteResource: module.deleteResource))),
                    child: FinanceSurface(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                  width: 43,
                                  height: 43,
                                  decoration: BoxDecoration(
                                      color: FinanceColors.primary
                                          .withValues(alpha: .2),
                                      borderRadius: BorderRadius.circular(14)),
                                  child: Icon(module.icon,
                                      color: FinanceColors.cyan)),
                              Row(children: [
                                Expanded(
                                    child: Text(module.name,
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w800))),
                                const Icon(Icons.arrow_forward_ios_rounded,
                                    size: 13, color: FinanceColors.muted)
                              ])
                            ])));
              }),
          const SizedBox(height: 12),
          ListTile(
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20)),
              tileColor: FinanceColors.surface,
              title: const Text('Compras detectadas'),
              subtitle:
                  const Text('Confirma avisos bancarios antes de registrarlos'),
              leading: const Icon(Icons.notifications_active_rounded,
                  color: FinanceColors.danger),
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const DetectionsPage()))),
        ]))));
  }
}

class _Module {
  const _Module(this.name, this.icon, this.loader, [this.deleteResource]);
  final String name;
  final IconData icon;
  final Future<List<dynamic>> Function(ApiClient) loader;
  final String? deleteResource;
}
