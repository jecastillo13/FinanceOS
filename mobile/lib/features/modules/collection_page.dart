import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';

class CollectionPage extends StatefulWidget {
  const CollectionPage({super.key, required this.title, required this.icon, required this.loader, this.deleteResource});
  final String title;
  final IconData icon;
  final Future<List<dynamic>> Function(ApiClient api) loader;
  final String? deleteResource;

  @override
  State<CollectionPage> createState() => _CollectionPageState();
}

class _CollectionPageState extends State<CollectionPage> {
  final _api = ApiClient();
  late Future<List<dynamic>> _items = widget.loader(_api);

  void _reload() => setState(() => _items = widget.loader(_api));

  String _headline(Map<String, dynamic> item) => '${item['nombre'] ?? item['descripcion'] ?? item['activo'] ?? item['categoria'] ?? 'Registro'}';
  String _detail(Map<String, dynamic> item) {
    final currency = '${item['moneda'] ?? 'COP'}';
    final value = item['saldo'] ?? item['valor'] ?? item['objetivo'] ?? item['precio_actual'] ?? item['tasa'];
    final parts = <String>[
      if (value is num) NumberFormat.currency(locale: 'es_CO', symbol: '$currency ', decimalDigits: currency == 'COP' ? 0 : 2).format(value),
      if (item['tipo'] != null) '${item['tipo']}',
      if (item['cuenta'] != null) '${item['cuenta']}',
      if (item['fecha'] != null) '${item['fecha']}',
      if (item['categoria'] != null && item['nombre'] != null) '${item['categoria']}',
    ];
    return parts.join(' · ');
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    final confirmed = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
      title: Text('Eliminar ${_headline(item)}'),
      content: const Text('Esta acción puede afectar información relacionada. ¿Deseas continuar?'),
      actions: [TextButton(onPressed: ()=>Navigator.pop(context, false), child: const Text('Cancelar')), FilledButton(onPressed: ()=>Navigator.pop(context, true), child: const Text('Eliminar'))],
    ));
    if (confirmed != true) return;
    try { await _api.eliminar(widget.deleteResource!, item['id'] as int); _reload(); }
    catch (error) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$error'))); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.title)),
    body: FinanceAurora(child: SafeArea(child: FutureBuilder<List<dynamic>>(
      future: _items,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('${snapshot.error}', textAlign: TextAlign.center)));
        final items = snapshot.data ?? const [];
        return RefreshIndicator(
          onRefresh: () async => _reload(),
          child: ListView(padding: const EdgeInsets.fromLTRB(18, 12, 18, 110), children: [
            FinanceSurface(child: Row(children: [Container(width: 52,height: 52,decoration:BoxDecoration(color:FinanceColors.primary.withValues(alpha:.2),borderRadius:BorderRadius.circular(16)),child:Icon(widget.icon,color:FinanceColors.cyan)),const SizedBox(width:14),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(widget.title,style:Theme.of(context).textTheme.titleLarge),Text('${items.length} registros sincronizados',style:const TextStyle(color:FinanceColors.muted))]))])),
            const SizedBox(height: 18),
            if (items.isEmpty) const FinanceSurface(child: Center(child: Padding(padding: EdgeInsets.all(20), child: Text('No hay registros todavía.', style: TextStyle(color: FinanceColors.muted)))))
            else ...items.map((raw) { final item = raw as Map<String,dynamic>; return Padding(padding:const EdgeInsets.only(bottom:10),child:FinanceSurface(padding:const EdgeInsets.all(14),child:Row(children:[Container(width:44,height:44,decoration:BoxDecoration(color:FinanceColors.surfaceHigh,borderRadius:BorderRadius.circular(14)),child:Icon(widget.icon,color:FinanceColors.primary)),const SizedBox(width:12),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(_headline(item),style:const TextStyle(fontSize:16,fontWeight:FontWeight.w800)),const SizedBox(height:4),Text(_detail(item),style:const TextStyle(color:FinanceColors.muted))])),if(widget.deleteResource!=null&&item['id']!=null)IconButton(onPressed:()=>_delete(item),icon:const Icon(Icons.delete_outline_rounded))])));}),
          ]),
        );
      },
    ))),
  );
}
