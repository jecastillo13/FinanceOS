import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../dashboard/dashboard_page.dart';
import '../detections/detections_page.dart';
import '../modules/collection_page.dart';
import '../receipts/receipt_scan_page.dart';
import '../reports/reports_page.dart';
import '../settings/settings_page.dart';

class MobileShell extends StatefulWidget {
  const MobileShell({super.key, required this.onLogout});
  final Future<void> Function() onLogout;
  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  final _key = GlobalKey<ScaffoldState>();
  int _index = 0;
  static final _pages = <Widget>[
    const DashboardPage(),
    CollectionPage(
        title: 'Ingresos y gastos',
        icon: Icons.receipt_long_rounded,
        loader: (a) => a.movimientos(),
        deleteResource: 'movimientos'),
    const ReceiptScanPage()
  ];

  void _collection(String title, IconData icon,
      Future<List<dynamic>> Function(ApiClient) loader,
      [String? resource]) {
    Navigator.pop(context);
    Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => CollectionPage(
                title: title,
                icon: icon,
                loader: loader,
                deleteResource: resource)));
  }

  Widget _drawer() {
    final now = DateTime.now();
    final entries = <({
      String title,
      String description,
      IconData icon,
      Future<List<dynamic>> Function(ApiClient) loader,
      String? resource
    })>[
      (
        title: 'Cuentas y saldos',
        description: 'Dónde está tu dinero',
        icon: Icons.account_balance_wallet_rounded,
        loader: (a) => a.cuentas(),
        resource: 'cuentas'
      ),
      (
        title: 'Tarjetas y compras',
        description: 'Medios de pago y avisos',
        icon: Icons.credit_card_rounded,
        loader: (a) => a.tarjetas(),
        resource: 'tarjetas'
      ),
      (
        title: 'Categorías',
        description: 'Clasificar ingresos y gastos',
        icon: Icons.sell_rounded,
        loader: (a) => a.categorias(),
        resource: 'categorias'
      ),
      (
        title: 'Pagos recurrentes',
        description: 'Obligaciones que se repiten',
        icon: Icons.event_repeat_rounded,
        loader: (a) => a.recurrentes(),
        resource: 'gastos-recurrentes'
      ),
      (
        title: 'Transferencias',
        description: 'Mover dinero entre cuentas',
        icon: Icons.swap_horiz_rounded,
        loader: (a) => a.transferencias(),
        resource: 'transferencias'
      ),
      (
        title: 'Presupuestos',
        description: 'Límites mensuales de gasto',
        icon: Icons.donut_large_rounded,
        loader: (a) => a.presupuestos(anio: now.year, mes: now.month),
        resource: 'presupuestos'
      ),
      (
        title: 'Metas',
        description: 'Ahorros y pagos futuros',
        icon: Icons.track_changes_rounded,
        loader: (a) => a.metas(),
        resource: 'metas'
      ),
      (
        title: 'Inversiones',
        description: 'Portafolio y rendimiento',
        icon: Icons.trending_up_rounded,
        loader: (a) async =>
            ((await a.inversiones())['posiciones'] as List<dynamic>? ?? []),
        resource: 'inversiones'
      ),
      (
        title: 'Monedas y tasas',
        description: 'Conversión a COP',
        icon: Icons.currency_exchange_rounded,
        loader: (a) => a.tasas(),
        resource: null
      )
    ];
    return Drawer(
        backgroundColor: FinanceColors.background,
        child: FinanceAurora(
            child: SafeArea(
                child: Column(children: [
          const Padding(
              padding: EdgeInsets.fromLTRB(20, 18, 20, 14),
              child: Row(children: [
                CircleAvatar(
                    radius: 23,
                    backgroundColor: FinanceColors.primary,
                    child: Icon(Icons.paid_rounded, color: Colors.white)),
                SizedBox(width: 12),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('FinanceOS',
                      style:
                          TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
                  Text('Finanzas claras',
                      style:
                          TextStyle(color: FinanceColors.muted, fontSize: 12))
                ])
              ])),
          const Divider(),
          ListTile(
              leading: const Icon(Icons.space_dashboard_rounded),
              title: const Text('Inicio'),
              subtitle: const Text('Resumen y próximos pasos'),
              onTap: () {
                Navigator.pop(context);
                setState(() => _index = 0);
              }),
          ListTile(
              leading: const Icon(Icons.receipt_long_rounded),
              title: const Text('Ingresos y gastos'),
              subtitle: const Text('Todo lo que entra y sale'),
              onTap: () {
                Navigator.pop(context);
                setState(() => _index = 1);
              }),
          Expanded(
              child: ListView(children: [
            ...entries.map((e) => ListTile(
                leading: Icon(e.icon),
                title: Text(e.title),
                subtitle: Text(e.description),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () =>
                    _collection(e.title, e.icon, e.loader, e.resource))),
            ListTile(
                leading: const Icon(Icons.document_scanner_rounded),
                title: const Text('Escanear factura'),
                onTap: () {
                  Navigator.pop(context);
                  setState(() => _index = 2);
                }),
            ListTile(
                leading: const Icon(Icons.notifications_active_rounded),
                title: const Text('Compras detectadas'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const DetectionsPage()));
                }),
            ListTile(
                leading: const Icon(Icons.analytics_rounded),
                title: const Text('Reportes'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const ReportsPage()));
                }),
            ListTile(
                leading: const Icon(Icons.settings_rounded),
                title: const Text('Configuración'),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(context,
                      MaterialPageRoute(builder: (_) => const SettingsPage()));
                })
          ])),
          Padding(
              padding: const EdgeInsets.all(14),
              child: Column(children: [
                const Row(children: [
                  Icon(Icons.circle, size: 9, color: FinanceColors.success),
                  SizedBox(width: 8),
                  Text('Sistema conectado',
                      style: TextStyle(
                          color: FinanceColors.success,
                          fontWeight: FontWeight.w700))
                ]),
                const SizedBox(height: 8),
                ListTile(
                    leading: const Icon(Icons.logout_rounded,
                        color: FinanceColors.danger),
                    title: const Text('Cerrar sesión'),
                    onTap: () {
                      Navigator.pop(context);
                      widget.onLogout();
                    })
              ]))
        ]))));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      key: _key,
      drawer: _drawer(),
      extendBody: true,
      body: IndexedStack(index: _index, children: _pages),
      bottomNavigationBar: SafeArea(
          minimum: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: Container(
              decoration: BoxDecoration(
                  color: const Color(0xF2131C32),
                  borderRadius: BorderRadius.circular(26),
                  border: Border.all(
                      color: FinanceColors.border.withValues(alpha: .72)),
                  boxShadow: const [
                    BoxShadow(
                        color: Color(0x66000000),
                        blurRadius: 28,
                        offset: Offset(0, 12))
                  ]),
              child: ClipRRect(
                  borderRadius: BorderRadius.circular(25),
                  child: NavigationBar(
                      selectedIndex: _index,
                      onDestinationSelected: (i) {
                        if (i == 3) {
                          _key.currentState?.openDrawer();
                        } else {
                          setState(() => _index = i);
                        }
                      },
                      height: 72,
                      backgroundColor: Colors.transparent,
                      indicatorColor:
                          FinanceColors.primary.withValues(alpha: .24),
                      destinations: const [
                        NavigationDestination(
                            icon: Icon(Icons.space_dashboard_outlined),
                            selectedIcon: Icon(Icons.space_dashboard_rounded),
                            label: 'Inicio'),
                        NavigationDestination(
                            icon: Icon(Icons.receipt_long_outlined),
                            selectedIcon: Icon(Icons.receipt_long_rounded),
                            label: 'Ingresos/gastos'),
                        NavigationDestination(
                            icon: Icon(Icons.document_scanner_outlined),
                            selectedIcon: Icon(Icons.document_scanner_rounded),
                            label: 'Escanear'),
                        NavigationDestination(
                            icon: Icon(Icons.menu_rounded),
                            selectedIcon: Icon(Icons.menu_open_rounded),
                            label: 'Menú')
                      ])))));
}
