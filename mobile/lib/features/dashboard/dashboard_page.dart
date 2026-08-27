import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../detections/detections_page.dart';
import '../receipts/receipt_scan_page.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final _api = ApiClient();
  late Future<_DashboardData> _data = _load();

  Future<_DashboardData> _load() async {
    final responses = await Future.wait([
      _api.resumenDashboard(),
      _api.cuentas(),
      _api.graficasDashboard(),
    ]);
    return _DashboardData(
      responses[0] as Map<String, dynamic>,
      responses[1] as List<dynamic>,
      responses[2] as Map<String, dynamic>,
    );
  }

  String _money(Object? value) =>
      NumberFormat.currency(locale: 'es_CO', symbol: r'$ ', decimalDigits: 0)
          .format((value as num?) ?? 0);

  void _refresh() => setState(() => _data = _load());

  @override
  Widget build(BuildContext context) => Scaffold(
        body: FinanceAurora(
          child: SafeArea(
            child: FutureBuilder<_DashboardData>(
              future: _data,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const _LoadingState();
                }
                if (snapshot.hasError) {
                  return _ErrorState(
                      error: snapshot.error.toString(), onRetry: _refresh);
                }
                return _DashboardContent(
                    data: snapshot.data!,
                    money: _money,
                    onRefresh: () async => _refresh());
              },
            ),
          ),
        ),
      );
}

class _DashboardContent extends StatelessWidget {
  const _DashboardContent(
      {required this.data, required this.money, required this.onRefresh});
  final _DashboardData data;
  final String Function(Object?) money;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final flujo = (data.graficas['flujo'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>();
    final categorias =
        (data.graficas['gastos_categoria'] as List<dynamic>? ?? const [])
            .cast<Map<String, dynamic>>();
    final insights = _buildInsights(data.resumen, data.graficas, money);
    return RefreshIndicator(
      onRefresh: onRefresh,
      color: FinanceColors.cyan,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics()),
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 34),
        children: [
          _TopBar(onRefresh: onRefresh),
          const SizedBox(height: 22),
          _HeroBalance(
              value: money(data.resumen['patrimonio']),
              balance: money(data.resumen['balance'])),
          const SizedBox(height: 14),
          Row(children: [
            Expanded(
                child: _MetricCard(
                    label: 'Ingresos',
                    value: money(data.resumen['ingresos']),
                    icon: Icons.south_west_rounded,
                    accent: FinanceColors.success)),
            const SizedBox(width: 12),
            Expanded(
                child: _MetricCard(
                    label: 'Gastos',
                    value: money(data.resumen['gastos']),
                    icon: Icons.north_east_rounded,
                    accent: FinanceColors.danger)),
          ]),
          const SizedBox(height: 12),
          _BalanceExplanation(
              income: money(data.resumen['ingresos']),
              expenses: money(data.resumen['gastos']),
              balance: money(data.resumen['balance']),
              negative: ((data.resumen['balance'] as num?) ?? 0) < 0),
          const SizedBox(height: 16),
          const _FinanceFlowCard(),
          const SizedBox(height: 16),
          _FinancialAnalysisCard(insights: insights),
          const SizedBox(height: 26),
          const _SectionTitle(
              title: 'Flujo de caja', subtitle: 'Últimos 6 meses'),
          const SizedBox(height: 10),
          FinanceSurface(
            child: SizedBox(
                height: 205,
                child: flujo.isEmpty
                    ? const _EmptyChart()
                    : CustomPaint(painter: _CashFlowPainter(flujo))),
          ),
          const SizedBox(height: 26),
          const _SectionTitle(
              title: 'Gastos principales', subtitle: 'Distribución del mes'),
          const SizedBox(height: 10),
          FinanceSurface(child: _CategoryBars(items: categorias, money: money)),
          const SizedBox(height: 26),
          _SectionTitle(
              title: 'Mis cuentas',
              subtitle: '${data.cuentas.length} productos'),
          const SizedBox(height: 10),
          ...data.cuentas.map((cuenta) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _AccountTile(
                  cuenta: cuenta as Map<String, dynamic>, money: money))),
        ],
      ),
    );
  }
}

class _BalanceExplanation extends StatelessWidget {
  const _BalanceExplanation(
      {required this.income,
      required this.expenses,
      required this.balance,
      required this.negative});
  final String income, expenses, balance;
  final bool negative;
  @override
  Widget build(BuildContext context) => FinanceSurface(
      padding: const EdgeInsets.all(14),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(negative ? Icons.info_outline_rounded : Icons.calculate_outlined,
            size: 20,
            color: negative ? FinanceColors.danger : FinanceColors.cyan),
        const SizedBox(width: 10),
        Expanded(
            child: Text(
                '$income en ingresos − $expenses en gastos = $balance de balance mensual. No es tu patrimonio.',
                style: const TextStyle(
                    color: FinanceColors.muted, fontSize: 12, height: 1.45)))
      ]));
}

List<_FinancialInsight> _buildInsights(Map<String, dynamic> summary,
    Map<String, dynamic> charts, String Function(Object?) money) {
  final income = (summary['ingresos'] as num?)?.toDouble() ?? 0;
  final expenses = (summary['gastos'] as num?)?.toDouble() ?? 0;
  final balance = (summary['balance'] as num?)?.toDouble() ?? 0;
  final patrimonio = (summary['patrimonio'] as num?)?.toDouble() ?? 0;
  final inversiones = (summary['inversiones_cop'] as num?)?.toDouble() ?? 0;
  final result = <_FinancialInsight>[];

  if (income == 0 && expenses == 0) {
    result.add(const _FinancialInsight('Sin flujo para evaluar',
        'Registra ingresos y gastos para calcular tu capacidad de ahorro.'));
  } else if (balance < 0) {
    result.add(_FinancialInsight('Gastas más de lo que ingresa',
        'El déficit de este mes es ${money(balance.abs())}.'));
  } else {
    final savings = income > 0 ? balance / income * 100 : 0;
    result.add(_FinancialInsight('Tu flujo mensual está en positivo',
        'Conservas ${money(balance)} (${savings.round()}% de tus ingresos).'));
  }

  final distribution = (charts['distribucion'] as List<dynamic>? ?? const [])
      .cast<Map<String, dynamic>>();
  final positiveTotal = distribution.fold<double>(
      0,
      (total, item) =>
          total + math.max(0, (item['saldo_cop'] as num?)?.toDouble() ?? 0));
  if (distribution.isNotEmpty && positiveTotal > 0) {
    final sorted = [...distribution]..sort((a, b) =>
        ((b['saldo_cop'] as num?) ?? 0)
            .compareTo((a['saldo_cop'] as num?) ?? 0));
    final largest = sorted.first;
    final percentage = (((largest['saldo_cop'] as num?)?.toDouble() ?? 0) /
            positiveTotal *
            100)
        .round();
    result.add(_FinancialInsight('Distribución de tus cuentas',
        '${largest['cuenta'] ?? 'Tu cuenta principal'} concentra $percentage% de tu dinero disponible.'));
  } else {
    result.add(const _FinancialInsight('Sin cuentas para analizar',
        'Crea una cuenta para medir liquidez y concentración.'));
  }

  final investmentRate = patrimonio > 0 ? inversiones / patrimonio * 100 : 0;
  result.add(_FinancialInsight(
      inversiones > 0 ? 'Patrimonio invertido' : 'Sin inversiones registradas',
      inversiones > 0
          ? '${investmentRate.round()}% de tu patrimonio está registrado como inversión.'
          : 'Puedes comenzar con una posición inicial sin inventar operaciones pasadas.'));
  return result;
}

class _FinanceFlowCard extends StatelessWidget {
  const _FinanceFlowCard();
  @override
  Widget build(BuildContext context) => FinanceSurface(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('CÓMO FUNCIONA FINANCEOS',
            style: TextStyle(
                color: FinanceColors.cyan,
                fontSize: 11,
                letterSpacing: 1.1,
                fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text('Un solo flujo, no módulos aislados',
            style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 14),
        const _FlowStep(
            1, 'Crea tus cuentas', 'Registra los saldos con los que empiezas.'),
        const _FlowStep(2, 'Registra ingresos y gastos',
            'Se actualizan cuentas, categorías y presupuestos.'),
        const _FlowStep(3, 'Planea y revisa',
            'Usa metas, inversiones y reportes para decidir.'),
      ]));
}

class _FlowStep extends StatelessWidget {
  const _FlowStep(this.number, this.title, this.detail);
  final int number;
  final String title, detail;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        CircleAvatar(
            radius: 16,
            backgroundColor: FinanceColors.primary.withValues(alpha: .2),
            child: Text('$number',
                style: const TextStyle(
                    color: FinanceColors.cyan, fontWeight: FontWeight.w800))),
        const SizedBox(width: 11),
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 3),
          Text(detail,
              style: const TextStyle(
                  color: FinanceColors.muted, fontSize: 12, height: 1.35)),
        ]))
      ]));
}

class _FinancialAnalysisCard extends StatelessWidget {
  const _FinancialAnalysisCard({required this.insights});
  final List<_FinancialInsight> insights;
  @override
  Widget build(BuildContext context) => FinanceSurface(
      accent: FinanceColors.primary,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Row(children: [
          Icon(Icons.auto_awesome_rounded, color: FinanceColors.cyan),
          SizedBox(width: 9),
          Expanded(
              child: Text('Análisis financiero local',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900))),
        ]),
        const SizedBox(height: 5),
        const Text(
            'Calculado en FinanceOS; tus datos no se envían a una IA externa.',
            style: TextStyle(
                color: FinanceColors.muted, fontSize: 12, height: 1.4)),
        const SizedBox(height: 14),
        ...insights.take(2).map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 11),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Icon(Icons.insights_rounded,
                  size: 18, color: FinanceColors.primary),
              const SizedBox(width: 9),
              Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Text(item.title,
                        style: const TextStyle(fontWeight: FontWeight.w800)),
                    const SizedBox(height: 3),
                    Text(item.detail,
                        style: const TextStyle(
                            color: FinanceColors.muted,
                            fontSize: 12,
                            height: 1.4)),
                  ]))
            ]))),
        TextButton.icon(
            onPressed: () => showModalBottomSheet<void>(
                context: context,
                showDragHandle: true,
                builder: (context) => SafeArea(
                        child: ListView(
                            padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
                            children: [
                          const Text('Qué está pasando con tu dinero',
                              style: TextStyle(
                                  fontSize: 22, fontWeight: FontWeight.w900)),
                          const SizedBox(height: 6),
                          const Text(
                              'Flujo, concentración y patrimonio invertido.',
                              style: TextStyle(color: FinanceColors.muted)),
                          const SizedBox(height: 16),
                          ...insights.map((item) => ListTile(
                              contentPadding: EdgeInsets.zero,
                              leading: const Icon(Icons.analytics_outlined,
                                  color: FinanceColors.cyan),
                              title: Text(item.title),
                              subtitle: Text(item.detail))),
                        ]))),
            icon: const Icon(Icons.open_in_full_rounded),
            label: const Text('Ver análisis completo')),
      ]));
}

class _FinancialInsight {
  const _FinancialInsight(this.title, this.detail);
  final String title, detail;
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.onRefresh});
  final Future<void> Function() onRefresh;
  @override
  Widget build(BuildContext context) => Row(children: [
        Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(15),
                gradient: const LinearGradient(
                    colors: [FinanceColors.primary, Color(0xFF584BE7)]),
                boxShadow: const [
                  BoxShadow(color: Color(0x557C83FF), blurRadius: 20)
                ]),
            child: const Icon(Icons.account_balance_wallet_rounded,
                color: Colors.white)),
        const SizedBox(width: 12),
        const Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('FinanceOS',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          Text('Centro financiero personal',
              style: TextStyle(color: FinanceColors.muted, fontSize: 12))
        ])),
        Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
            decoration: BoxDecoration(
                color: FinanceColors.success.withValues(alpha: .10),
                border: Border.all(
                    color: FinanceColors.success.withValues(alpha: .25)),
                borderRadius: BorderRadius.circular(20)),
            child: const Row(children: [
              Icon(Icons.circle, size: 7, color: FinanceColors.success),
              SizedBox(width: 6),
              Text('Activo',
                  style: TextStyle(
                      color: FinanceColors.success,
                      fontSize: 11,
                      fontWeight: FontWeight.w700))
            ])),
        IconButton(
            tooltip: 'Compras detectadas',
            onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const DetectionsPage())),
            icon: const Icon(Icons.notifications_active_rounded)),
        IconButton(
            tooltip: 'Escanear factura',
            onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const ReceiptScanPage())),
            icon: const Icon(Icons.document_scanner_rounded)),
        IconButton(
            onPressed: onRefresh, icon: const Icon(Icons.refresh_rounded)),
      ]);
}

class _HeroBalance extends StatelessWidget {
  const _HeroBalance({required this.value, required this.balance});
  final String value, balance;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(28),
            gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFF5964E8), Color(0xFF273C87)]),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x553D49C6),
                  blurRadius: 34,
                  offset: Offset(0, 16))
            ]),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Row(children: [
            Text('PATRIMONIO TOTAL',
                style: TextStyle(
                    fontSize: 11,
                    letterSpacing: 1.2,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFFC9D2FF))),
            Spacer(),
            Icon(Icons.auto_awesome_rounded, color: FinanceColors.cyan)
          ]),
          const SizedBox(height: 18),
          FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: Text(value,
                  style: const TextStyle(
                      fontSize: 34,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -1.2))),
          const SizedBox(height: 18),
          Row(children: [
            const Icon(Icons.analytics_rounded,
                size: 18, color: FinanceColors.success),
            const SizedBox(width: 7),
            Text('Balance mensual  $balance',
                style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFFDCE3FF),
                    fontWeight: FontWeight.w600))
          ]),
        ]),
      );
}

class _MetricCard extends StatelessWidget {
  const _MetricCard(
      {required this.label,
      required this.value,
      required this.icon,
      required this.accent});
  final String label, value;
  final IconData icon;
  final Color accent;
  @override
  Widget build(BuildContext context) => FinanceSurface(
      accent: accent,
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
                color: accent.withValues(alpha: .14),
                borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, size: 19, color: accent)),
        const SizedBox(height: 13),
        Text(label,
            style: const TextStyle(color: FinanceColors.muted, fontSize: 12)),
        const SizedBox(height: 4),
        FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(value,
                style: const TextStyle(
                    fontSize: 18, fontWeight: FontWeight.w800))),
      ]));
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, required this.subtitle});
  final String title, subtitle;
  @override
  Widget build(BuildContext context) =>
      Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        Expanded(
            child: Text(title, style: Theme.of(context).textTheme.titleLarge)),
        Text(subtitle,
            style: const TextStyle(color: FinanceColors.muted, fontSize: 12))
      ]);
}

class _CategoryBars extends StatelessWidget {
  const _CategoryBars({required this.items, required this.money});
  final List<Map<String, dynamic>> items;
  final String Function(Object?) money;
  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return const Padding(
          padding: EdgeInsets.symmetric(vertical: 22),
          child: Center(
              child: Text('Aún no hay gastos para analizar.',
                  style: TextStyle(color: FinanceColors.muted))));
    }
    final maxValue = items
        .map((e) => (e['valor'] as num?)?.toDouble() ?? 0)
        .fold<double>(0, (actual, value) => math.max(actual, value));
    return Column(
        children: items.take(5).map((item) {
      final value = (item['valor'] as num?)?.toDouble() ?? 0;
      final label = item['categoría']?.toString() ?? 'Sin categoría';
      return Padding(
          padding: const EdgeInsets.only(bottom: 15),
          child: Column(children: [
            Row(children: [
              Expanded(
                  child: Text(label,
                      style: const TextStyle(fontWeight: FontWeight.w700))),
              Text(money(value),
                  style:
                      const TextStyle(color: FinanceColors.muted, fontSize: 12))
            ]),
            const SizedBox(height: 7),
            ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: LinearProgressIndicator(
                    value: maxValue == 0 ? 0 : value / maxValue,
                    minHeight: 7,
                    backgroundColor:
                        FinanceColors.border.withValues(alpha: .35),
                    valueColor:
                        const AlwaysStoppedAnimation(FinanceColors.primary))),
          ]));
    }).toList());
  }
}

class _AccountTile extends StatelessWidget {
  const _AccountTile({required this.cuenta, required this.money});
  final Map<String, dynamic> cuenta;
  final String Function(Object?) money;
  @override
  Widget build(BuildContext context) => FinanceSurface(
      padding: const EdgeInsets.all(15),
      child: Row(children: [
        Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
                gradient: const LinearGradient(
                    colors: [FinanceColors.primary, Color(0xFF4B65D4)]),
                borderRadius: BorderRadius.circular(15)),
            child: const Icon(Icons.account_balance_rounded,
                color: Colors.white, size: 21)),
        const SizedBox(width: 13),
        Expanded(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(cuenta['nombre']?.toString() ?? 'Cuenta',
              style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 3),
          Text(cuenta['tipo']?.toString() ?? '',
              style: const TextStyle(color: FinanceColors.muted, fontSize: 12))
        ])),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('${cuenta['moneda'] ?? 'COP'}',
              style: const TextStyle(
                  color: FinanceColors.cyan,
                  fontSize: 10,
                  fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(money(cuenta['saldo']),
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14))
        ]),
      ]));
}

class _CashFlowPainter extends CustomPainter {
  _CashFlowPainter(this.data);
  final List<Map<String, dynamic>> data;

  @override
  void paint(Canvas canvas, Size size) {
    final values = data
        .expand((row) => [
              (row['ingresos'] as num?)?.toDouble() ?? 0,
              (row['gastos'] as num?)?.toDouble() ?? 0
            ])
        .toList();
    final maxValue =
        values.fold<double>(1, (actual, value) => math.max(actual, value));
    final chart = Rect.fromLTWH(8, 12, size.width - 16, size.height - 34);
    for (var i = 0; i < 4; i++) {
      final y = chart.top + chart.height * i / 3;
      canvas.drawLine(
          Offset(chart.left, y),
          Offset(chart.right, y),
          Paint()
            ..color = FinanceColors.border.withValues(alpha: .28)
            ..strokeWidth = 1);
    }
    _drawSeries(canvas, chart, maxValue, 'ingresos', FinanceColors.success);
    _drawSeries(canvas, chart, maxValue, 'gastos', FinanceColors.danger);
  }

  void _drawSeries(
      Canvas canvas, Rect chart, double maxValue, String key, Color color) {
    if (data.isEmpty) return;
    final path = Path();
    for (var i = 0; i < data.length; i++) {
      final x = chart.left +
          (data.length == 1 ? 0 : chart.width * i / (data.length - 1));
      final value = (data[i][key] as num?)?.toDouble() ?? 0;
      final y = chart.bottom - chart.height * value / maxValue;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    canvas.drawPath(
        path,
        Paint()
          ..color = color.withValues(alpha: .18)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 9
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10));
    canvas.drawPath(
        path,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeCap = StrokeCap.round
          ..strokeJoin = StrokeJoin.round
          ..strokeWidth = 3);
  }

  @override
  bool shouldRepaint(covariant _CashFlowPainter oldDelegate) =>
      oldDelegate.data != data;
}

class _LoadingState extends StatelessWidget {
  const _LoadingState();
  @override
  Widget build(BuildContext context) =>
      const Center(child: CircularProgressIndicator(color: FinanceColors.cyan));
}

class _EmptyChart extends StatelessWidget {
  const _EmptyChart();
  @override
  Widget build(BuildContext context) => const Center(
      child: Text('Registra movimientos para activar la gráfica.',
          style: TextStyle(color: FinanceColors.muted)));
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.error, required this.onRetry});
  final String error;
  final VoidCallback onRetry;
  @override
  Widget build(BuildContext context) => Center(
      child: Padding(
          padding: const EdgeInsets.all(30),
          child: FinanceSurface(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.cloud_off_rounded,
                size: 54, color: FinanceColors.danger),
            const SizedBox(height: 16),
            const Text('No pudimos conectar con FinanceOS.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Text(error,
                textAlign: TextAlign.center,
                style: const TextStyle(color: FinanceColors.muted)),
            const SizedBox(height: 18),
            FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Reintentar'))
          ]))));
}

class _DashboardData {
  const _DashboardData(this.resumen, this.cuentas, this.graficas);
  final Map<String, dynamic> resumen;
  final List<dynamic> cuentas;
  final Map<String, dynamic> graficas;
}
