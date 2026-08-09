import 'package:flutter/material.dart';

import 'core/design_system.dart';
import 'features/dashboard/dashboard_page.dart';

void main() => runApp(const FinanceOSMobile());

class FinanceOSMobile extends StatelessWidget {
  const FinanceOSMobile({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'FinanceOS',
        debugShowCheckedModeBanner: false,
        theme: FinanceTheme.dark,
        home: const DashboardPage(),
      );
}
