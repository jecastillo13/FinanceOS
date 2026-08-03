import 'package:flutter/material.dart';

import 'features/dashboard/dashboard_page.dart';

void main() => runApp(const FinanceOSMobile());

class FinanceOSMobile extends StatelessWidget {
  const FinanceOSMobile({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'FinanceOS',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF7165F8), brightness: Brightness.dark),
        ),
        home: const DashboardPage(),
      );
}
