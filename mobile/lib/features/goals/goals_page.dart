import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../modules/record_form_page.dart';

class GoalsPage extends StatefulWidget {
  const GoalsPage({super.key});

  @override
  State<GoalsPage> createState() => _GoalsPageState();
}

class _GoalsPageState extends State<GoalsPage> {
  final _api = ApiClient();
  late Future<List<dynamic>> _goals = _api.metas();
  List<dynamic> _accounts = [], _categories = [];

  @override
  void initState() {
    super.initState();
    _loadOptions();
  }

  Future<void> _loadOptions() async {
    final result = await Future.wait([_api.cuentas(), _api.categorias()]);
    if (!mounted) return;
    setState(() {
      _accounts = result[0];
      _categories = result[1]
          .where((item) => item['tipo']?.toString() == 'Gasto')
          .toList();
    });
  }

  void _reload() => setState(() => _goals = _api.metas());

  String _money(Object? value, [String currency = 'COP']) =>
      NumberFormat.currency(
              locale: 'es_CO', symbol: '$currency ', decimalDigits: 0)
          .format((value as num?) ?? 0);

  Future<void> _create() async {
    final changed = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
            builder: (_) => const RecordFormPage(
                resource: 'metas', title: 'Meta')));
    if (changed == true) _reload();
  }

  Future<void> _contribute(Map<String, dynamic> goal) async {
    final value = TextEditingController();
    final note = TextEditingController();
    final accepted = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
              title: Text('Anotar ahorro para ${goal['nombre']}'),
              content: SingleChildScrollView(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                Container(
                    padding: const EdgeInsets.all(13),
                    decoration: BoxDecoration(
                        color: FinanceColors.primary.withValues(alpha: .09),
                        borderRadius: BorderRadius.circular(15)),
                    child: const Text(
                        'No moverá dinero. Solo anotará cuánto ya separaste. Si lo moviste a otra cuenta, registra también una transferencia.',
                        style: TextStyle(color: FinanceColors.muted))),
                const SizedBox(height: 14),
                TextField(
                    controller: value,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                        labelText: 'Valor reservado (${goal['moneda']})')),
                const SizedBox(height: 10),
                TextField(
                    controller: note,
                    decoration: const InputDecoration(
                        labelText: 'Dónde lo reservaste')),
              ])),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    onPressed: () => Navigator.pop(context, true),
                    child: const Text('Guardar ahorro anotado'))
              ],
            ));
    if (accepted != true) return;
    try {
      await _api.aportarMeta(
          metaId: goal['id'] as int,
          valor: double.parse(value.text.replaceAll(',', '.')),
          fecha: DateTime.now(),
          descripcion: note.text);
      _reload();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      value.dispose();
      note.dispose();
    }
  }

  Future<void> _pay(Map<String, dynamic> goal) async {
    if (_accounts.isEmpty || _categories.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Necesitas una cuenta y una categoría de gasto.')));
      return;
    }
    final value = TextEditingController();
    var account = _accounts.first['id'] as int;
    var category = _categories.first['id'] as int;
    final accepted = await showDialog<bool>(
        context: context,
        builder: (context) => StatefulBuilder(
            builder: (context, setDialogState) => AlertDialog(
                  title: Text('Pagar ${goal['nombre']} desde una cuenta'),
                  content: SingleChildScrollView(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                    Container(
                        padding: const EdgeInsets.all(13),
                        decoration: BoxDecoration(
                            color: FinanceColors.success.withValues(alpha: .08),
                            borderRadius: BorderRadius.circular(15)),
                        child: const Text(
                            'Sí moverá dinero: descontará la cuenta seleccionada y registrará el gasto real.',
                            style: TextStyle(color: FinanceColors.muted))),
                    const SizedBox(height: 14),
                    TextField(
                        controller: value,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                            labelText: 'Valor (${goal['moneda']})')),
                    const SizedBox(height: 10),
                    DropdownButtonFormField<int>(
                        initialValue: account,
                        decoration:
                            const InputDecoration(labelText: 'Cuenta que pagará'),
                        items: _accounts
                            .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text('${item['nombre']} (${item['moneda']})')))
                            .toList(),
                        onChanged: (id) => setDialogState(() => account = id!)),
                    const SizedBox(height: 10),
                    DropdownButtonFormField<int>(
                        initialValue: category,
                        decoration: const InputDecoration(
                            labelText: 'Categoría del gasto'),
                        items: _categories
                            .map((item) => DropdownMenuItem<int>(
                                value: item['id'] as int,
                                child: Text('${item['nombre']}')))
                            .toList(),
                        onChanged: (id) => setDialogState(() => category = id!)),
                  ])),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Confirmar pago real'))
                  ],
                )));
    if (accepted != true) return;
    try {
      await _api.pagarMeta(
          metaId: goal['id'] as int,
          valor: double.parse(value.text.replaceAll(',', '.')),
          fecha: DateTime.now(),
          cuentaId: account,
          categoriaId: category,
          descripcion: 'Pago de ${goal['nombre']}');
      _reload();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$error')));
      }
    } finally {
      value.dispose();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Metas de ahorro y pagos')),
      floatingActionButton: FloatingActionButton.extended(
          onPressed: _create,
          icon: const Icon(Icons.add_rounded),
          label: const Text('Crear meta')),
      body: FinanceAurora(
          child: SafeArea(
              child: FutureBuilder<List<dynamic>>(
                  future: _goals,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snapshot.hasError) {
                      return Center(child: Text('${snapshot.error}'));
                    }
                    final goals = snapshot.data ?? const [];
                    return RefreshIndicator(
                        onRefresh: () async => _reload(),
                        child: ListView(
                            padding: const EdgeInsets.fromLTRB(18, 12, 18, 110),
                            children: [
                              FinanceSurface(
                                  child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                    Text('Dos acciones diferentes',
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleLarge),
                                    const SizedBox(height: 7),
                                    const Text(
                                        'Anotar ahorro no cambia saldos. Pagar sí descuenta una cuenta y crea el gasto.',
                                        style: TextStyle(
                                            color: FinanceColors.muted,
                                            height: 1.45))
                                  ])),
                              const SizedBox(height: 14),
                              if (goals.isEmpty)
                                const FinanceSurface(
                                    child: Padding(
                                        padding: EdgeInsets.all(20),
                                        child: Text('Crea tu primera meta para comenzar.')))
                              else
                                ...goals.map((raw) => _GoalCard(
                                    goal: raw as Map<String, dynamic>,
                                    money: _money,
                                    contribute: () => _contribute(raw),
                                    pay: () => _pay(raw))),
                            ]));
                  }))));
}

class _GoalCard extends StatelessWidget {
  const _GoalCard(
      {required this.goal,
      required this.money,
      required this.contribute,
      required this.pay});
  final Map<String, dynamic> goal;
  final String Function(Object?, [String]) money;
  final VoidCallback contribute, pay;

  @override
  Widget build(BuildContext context) {
    final currency = goal['moneda']?.toString() ?? 'COP';
    final percentage = ((goal['porcentaje'] as num?) ?? 0).clamp(0, 100) / 100;
    return Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: FinanceSurface(
            accent: FinanceColors.primary,
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.track_changes_rounded,
                    color: FinanceColors.cyan),
                const SizedBox(width: 10),
                Expanded(
                    child: Text('${goal['nombre']}',
                        style: const TextStyle(
                            fontSize: 20, fontWeight: FontWeight.w900))),
                Text('${(percentage * 100).round()}% pagado',
                    style: const TextStyle(
                        color: FinanceColors.success,
                        fontWeight: FontWeight.w800))
              ]),
              if ('${goal['descripcion'] ?? ''}'.isNotEmpty) ...[
                const SizedBox(height: 5),
                Text('${goal['descripcion']}',
                    style: const TextStyle(color: FinanceColors.muted))
              ],
              const SizedBox(height: 15),
              LinearProgressIndicator(
                  value: percentage.toDouble(), minHeight: 8,
                  borderRadius: BorderRadius.circular(20)),
              const SizedBox(height: 16),
              Row(children: [
                Expanded(child: _Amount('Ahorro anotado',
                    money(goal['aportado'], currency), 'No modifica cuentas')),
                const SizedBox(width: 10),
                Expanded(child: _Amount('Pagado realmente',
                    money(goal['pagado'], currency), 'Sí descuenta una cuenta')),
              ]),
              const SizedBox(height: 10),
              _Amount('Falta por pagar', money(goal['pendiente'], currency),
                  'Objetivo: ${money(goal['objetivo'], currency)}'),
              const SizedBox(height: 16),
              FilledButton.tonalIcon(
                  onPressed: contribute,
                  icon: const Icon(Icons.savings_outlined),
                  label: const Text('Anotar ahorro reservado · no mueve dinero')),
              const SizedBox(height: 9),
              FilledButton.icon(
                  onPressed: pay,
                  icon: const Icon(Icons.account_balance_wallet_outlined),
                  label: const Text('Pagar desde una cuenta · registra gasto')),
            ])));
  }
}

class _Amount extends StatelessWidget {
  const _Amount(this.label, this.value, this.detail);
  final String label, value, detail;
  @override
  Widget build(BuildContext context) => Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: FinanceColors.surfaceHigh.withValues(alpha: .52),
          borderRadius: BorderRadius.circular(14)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label,
            style: const TextStyle(color: FinanceColors.muted, fontSize: 11)),
        const SizedBox(height: 5),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w900)),
        const SizedBox(height: 3),
        Text(detail,
            style: const TextStyle(color: FinanceColors.muted, fontSize: 10))
      ]));
}
