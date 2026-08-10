import 'package:flutter/material.dart';

import '../../core/design_system.dart';
import '../dashboard/dashboard_page.dart';
import '../detections/detections_page.dart';
import '../receipts/receipt_scan_page.dart';

/// Navegacion principal de FinanceOS para telefonos.
///
/// IndexedStack conserva el estado y la posicion de desplazamiento de cada
/// modulo al cambiar de seccion.
class MobileShell extends StatefulWidget {
  const MobileShell({super.key});

  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  int _selectedIndex = 0;

  static const _pages = <Widget>[
    DashboardPage(),
    ReceiptScanPage(),
    DetectionsPage(),
  ];

  @override
  Widget build(BuildContext context) => Scaffold(
        extendBody: true,
        body: IndexedStack(index: _selectedIndex, children: _pages),
        bottomNavigationBar: SafeArea(
          minimum: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: const Color(0xF2131C32),
              borderRadius: BorderRadius.circular(26),
              border: Border.all(color: FinanceColors.border.withValues(alpha: .72)),
              boxShadow: const [
                BoxShadow(color: Color(0x66000000), blurRadius: 28, offset: Offset(0, 12)),
                BoxShadow(color: Color(0x227C83FF), blurRadius: 22),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(25),
              child: NavigationBar(
                selectedIndex: _selectedIndex,
                onDestinationSelected: (index) => setState(() => _selectedIndex = index),
                height: 72,
                backgroundColor: Colors.transparent,
                indicatorColor: FinanceColors.primary.withValues(alpha: .24),
                labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
                destinations: const [
                  NavigationDestination(
                    icon: Icon(Icons.space_dashboard_outlined),
                    selectedIcon: Icon(Icons.space_dashboard_rounded, color: FinanceColors.text),
                    label: 'Inicio',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.document_scanner_outlined),
                    selectedIcon: Icon(Icons.document_scanner_rounded, color: FinanceColors.text),
                    label: 'Escanear',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.notifications_none_rounded),
                    selectedIcon: Icon(Icons.notifications_active_rounded, color: FinanceColors.text),
                    label: 'Detectadas',
                  ),
                ],
              ),
            ),
          ),
        ),
      );
}
