import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';

class DetectionsPage extends StatefulWidget {
  const DetectionsPage({super.key});
  @override
  State<DetectionsPage> createState() => _DetectionsPageState();
}

class _DetectionsPageState extends State<DetectionsPage> {
  final _api = ApiClient(), _text = TextEditingController();
  late Future<List<dynamic>> _items = _api.detecciones();
  bool _busy = false;
  void _reload() => setState(() => _items = _api.detecciones());
  Future<void> _analyze() async {
    if (_text.text.trim().isEmpty) return;
    setState(() => _busy = true);
    try {
      await _api.detectarOperacion(_text.text);
      _text.clear();
      _reload();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Compras detectadas')),
      body: FinanceAurora(
          child: SafeArea(
              child: ListView(padding: const EdgeInsets.all(18), children: [
        FinanceSurface(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Row(children: [
            Icon(Icons.auto_awesome_rounded, color: FinanceColors.cyan),
            SizedBox(width: 10),
            Text('Analizar aviso bancario',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800))
          ]),
          const SizedBox(height: 8),
          const Text(
              'Pega una notificación o SMS. FinanceOS nunca guardará la compra sin tu confirmación.',
              style: TextStyle(color: FinanceColors.muted)),
          const SizedBox(height: 14),
          TextField(
              controller: _text,
              maxLines: 5,
              decoration: const InputDecoration(
                  hintText: 'Compra por COP \$75.900 en...')),
          const SizedBox(height: 12),
          SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                  onPressed: _busy ? null : _analyze,
                  icon: const Icon(Icons.radar_rounded),
                  label: const Text('Analizar')))
        ])),
        const SizedBox(height: 22),
        const Text('Pendientes',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
        const SizedBox(height: 10),
        FutureBuilder<List<dynamic>>(
            future: _items,
            builder: (context, s) {
              if (!s.hasData)
                return const Center(child: CircularProgressIndicator());
              if (s.data!.isEmpty)
                return const FinanceSurface(
                    child: Text('No hay compras pendientes.',
                        style: TextStyle(color: FinanceColors.muted)));
              return Column(
                  children: s.data!.map((raw) {
                final d = raw as Map<String, dynamic>;
                return Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: FinanceSurface(
                        child: Row(children: [
                      Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                              color:
                                  FinanceColors.primary.withValues(alpha: .15),
                              borderRadius: BorderRadius.circular(14)),
                          child: const Icon(Icons.notifications_active_rounded,
                              color: FinanceColors.cyan)),
                      const SizedBox(width: 12),
                      Expanded(
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                            Text(d['comercio'] ?? 'Compra',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w800)),
                            Text('${d['moneda']} ${d['valor']}',
                                style: const TextStyle(
                                    fontSize: 18, fontWeight: FontWeight.w900)),
                            Text(d['tipo_sugerido'] ?? 'Tipo por confirmar',
                                style: const TextStyle(
                                    color: FinanceColors.muted, fontSize: 12))
                          ])),
                      IconButton(
                          tooltip: 'Descartar',
                          onPressed: () async {
                            await _api.descartarDeteccion(d['id']);
                            _reload();
                          },
                          icon: const Icon(Icons.close_rounded))
                    ])));
              }).toList());
            })
      ]))));
  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }
}
