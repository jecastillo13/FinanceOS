import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';

class RecordFormPage extends StatefulWidget {
  const RecordFormPage(
      {super.key, required this.resource, required this.title, this.initial});
  final String resource, title;
  final Map<String, dynamic>? initial;
  @override
  State<RecordFormPage> createState() => _RecordFormPageState();
}

class _RecordFormPageState extends State<RecordFormPage> {
  final _api = ApiClient(), _form = GlobalKey<FormState>();
  final Map<String, TextEditingController> _values = {};
  List<dynamic> _accounts = [], _categories = [];
  bool _busy = false, _loading = true;
  bool _initialPosition = true;
  bool _active = true;
  String? _error;
  int? _account, _destination, _category;
  String _type = 'Gasto', _currency = 'COP', _frequency = 'Mensual';
  TextEditingController c(String name, [String initial = '']) =>
      _values.putIfAbsent(name, () => TextEditingController(text: initial));
  String get today => DateTime.now().toIso8601String().split('T').first;

  @override
  void initState() {
    super.initState();
    final initial = widget.initial;
    if (initial != null) {
      _type = '${initial['tipo'] ?? _type}';
      _currency = '${initial['moneda'] ?? _currency}';
      _frequency = '${initial['frecuencia'] ?? _frequency}';
      _initialPosition = initial['es_posicion_inicial'] != false;
      _active = initial['activa'] != false;
    }
    _load();
  }

  String initial(String key, [String fallback = '']) {
    final value = widget.initial?[key];
    return value == null ? fallback : '$value';
  }

  Future<void> _load() async {
    try {
      if (widget.resource == 'inversiones') _currency = 'USD';
      final result = await Future.wait([_api.cuentas(), _api.categorias()]);
      _accounts = result[0];
      _categories = result[1];
      _account = widget.initial?['cuenta_id'] as int? ??
          widget.initial?['cuenta_origen_id'] as int? ??
          (_accounts.isEmpty ? null : _accounts.first['id'] as int);
      _destination =
          _accounts.length > 1 ? _accounts[1]['id'] as int : _account;
      _category = widget.initial?['categoria_id'] as int? ??
          (_categories.isEmpty ? null : _categories.first['id'] as int);
    } catch (error) {
      _error = '$error';
    }
    if (mounted) setState(() => _loading = false);
  }

  Widget field(String label, String name,
          {TextInputType? keyboard, String? initial, bool required = true}) =>
      Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: TextFormField(
              controller: c(name, initial ?? ''),
              keyboardType: keyboard,
              decoration: InputDecoration(labelText: label),
              validator: (value) => required && value!.trim().isEmpty
                  ? 'Campo requerido'
                  : null));
  Widget select(String label, String value, List<String> options,
          ValueChanged<String> change) =>
      Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: DropdownButtonFormField<String>(
              initialValue: value,
              decoration: InputDecoration(labelText: label),
              items: options
                  .map((x) => DropdownMenuItem(value: x, child: Text(x)))
                  .toList(),
              onChanged: (x) => change(x!)));
  Widget accountSelect(String label, {bool destination = false}) => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<int>(
          initialValue: destination ? _destination : _account,
          decoration: InputDecoration(labelText: label),
          items: _accounts
              .where((x) =>
                  x['activa'] != false ||
                  x['id'] == _account ||
                  x['id'] == _destination)
              .map((x) => DropdownMenuItem<int>(
                  value: x['id'] as int,
                  child: Text('${x['nombre']} (${x['moneda']})')))
              .toList(),
          onChanged: (x) =>
              setState(() => destination ? _destination = x : _account = x)));
  Widget categorySelect() => Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<int>(
          initialValue: _category,
          decoration: const InputDecoration(labelText: 'Categoría'),
          items: _categories
              .map((x) => DropdownMenuItem<int>(
                  value: x['id'] as int,
                  child: Text('${x['nombre']} · ${x['tipo']}')))
              .toList(),
          onChanged: (x) => setState(() => _category = x)));

  List<Widget> _fields() {
    switch (widget.resource) {
      case 'cuentas':
        return [
          field('Nombre', 'nombre', initial: initial('nombre')),
          field('Entidad o institución', 'institucion',
              initial: initial('institucion'), required: false),
          select(
              'Tipo',
              _type,
              ['Ahorros', 'Corriente', 'Efectivo', 'Inversión'],
              (x) => _type = x),
          select('Moneda', _currency, ['COP', 'USD', 'EUR'],
              (x) => setState(() => _currency = x)),
          if (widget.initial == null)
            field('Saldo inicial', 'valor',
                keyboard: TextInputType.number, initial: '0'),
          if (widget.initial != null)
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const Text('Cuenta activa'),
              subtitle: const Text(
                  'Las cuentas desactivadas conservan su historial, pero no reciben movimientos.'),
              value: _active,
              onChanged: (value) => setState(() => _active = value),
            )
        ];
      case 'categorias':
        return [
          field('Nombre', 'nombre', initial: initial('nombre')),
          field('Grupo', 'grupo', initial: initial('grupo', 'Otros')),
          select(
              'Tipo',
              _type,
              ['Gasto', 'Ingreso', 'Ahorro', 'Inversión', 'Transferencia'],
              (x) => setState(() => _type = x)),
          field('Icono', 'icono', initial: initial('icono', '🏷️'))
        ];
      case 'movimientos':
        return [
          field('Descripción', 'nombre', initial: initial('descripcion')),
          field('Valor', 'valor',
              keyboard: TextInputType.number,
              initial: widget.initial == null
                  ? ''
                  : '${((widget.initial!['valor'] as num?) ?? 0).abs()}'),
          field('Fecha', 'fecha', initial: initial('fecha', today)),
          accountSelect('Cuenta'),
          categorySelect(),
          field('Observaciones', 'nota',
              initial: initial('observaciones'), required: false)
        ];
      case 'gastos-recurrentes':
        return [
          field('Nombre', 'nombre', initial: initial('nombre')),
          field('Valor', 'valor',
              keyboard: TextInputType.number, initial: initial('valor')),
          select(
              'Frecuencia',
              _frequency,
              ['Mensual', 'Quincenal', 'Semanal', 'Anual'],
              (x) => setState(() => _frequency = x)),
          field('Próximo pago', 'fecha',
              initial: initial('proxima_fecha_pago', today)),
          categorySelect()
        ];
      case 'transferencias':
        return [
          field('Fecha', 'fecha', initial: today),
          accountSelect('Cuenta de origen'),
          accountSelect('Cuenta de destino', destination: true),
          field('Valor', 'valor', keyboard: TextInputType.number),
          field('Descripción', 'nota', required: false)
        ];
      case 'presupuestos':
        return [
          categorySelect(),
          field('Valor máximo', 'valor', keyboard: TextInputType.number)
        ];
      case 'metas':
        return [
          field('Nombre', 'nombre'),
          field('Objetivo', 'valor', keyboard: TextInputType.number),
          select('Moneda', _currency, ['COP', 'USD', 'EUR'],
              (x) => setState(() => _currency = x)),
          field('Fecha límite', 'fecha', initial: today),
          field('Descripción', 'nota', required: false)
        ];
      case 'inversiones':
        return [
          SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const Text('Ya tenía esta inversión'),
              subtitle: Text(_initialPosition
                  ? 'Saldo inicial: no descontará una cuenta.'
                  : 'Compra nueva: el costo saldrá de una cuenta y no será un gasto.'),
              value: _initialPosition,
              onChanged: (value) => setState(() => _initialPosition = value)),
          if (!_initialPosition) accountSelect('Cuenta que paga'),
          field('Fecha de compra o saldo inicial', 'fecha',
              initial: initial('fecha_apertura', today)),
          field('Activo', 'nombre', initial: initial('activo')),
          field('Tipo de activo', 'tipo', initial: initial('tipo', 'ETF')),
          field('Cantidad', 'cantidad',
              keyboard: TextInputType.number, initial: initial('cantidad')),
          field('Costo de compra', 'compra',
              keyboard: TextInputType.number,
              initial: initial('precio_compra')),
          field('Valor actual', 'actual',
              keyboard: TextInputType.number,
              initial: initial('precio_actual')),
          select('Moneda', _currency, ['USD', 'COP', 'EUR'],
              (x) => setState(() => _currency = x)),
          field('Broker', 'nota', initial: initial('broker'), required: false)
        ];
      case 'tarjetas':
        return [
          field('Nombre', 'nombre'),
          field('Banco', 'nota'),
          field('Últimos cuatro dígitos', 'ultimos',
              keyboard: TextInputType.number),
          select('Tipo', 'Débito', ['Débito', 'Crédito'],
              (x) => setState(() => _type = x)),
          select('Moneda', _currency, ['COP', 'USD', 'EUR'],
              (x) => setState(() => _currency = x)),
          accountSelect('Cuenta vinculada')
        ];
      default:
        return [];
    }
  }

  double number(String name) => double.parse(c(name).text.replaceAll(',', '.'));
  Future<void> _save() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      switch (widget.resource) {
        case 'cuentas':
          final body = {
            'nombre': c('nombre').text,
            'tipo': _type,
            'moneda': _currency,
            'color': '${widget.initial?['color'] ?? '#6255e7'}',
            'icono': '${widget.initial?['icono'] ?? '🏦'}',
            'institucion': c('institucion').text,
            'activa': _active,
          };
          if (widget.initial == null) {
            await _api.crearCuenta({...body, 'saldo': number('valor')});
          } else {
            await _api.actualizar(
                'cuentas', widget.initial!['id'] as int, body);
          }
          break;
        case 'categorias':
          final body = {
            'nombre': c('nombre').text,
            'grupo': c('grupo').text,
            'tipo': _type,
            'icono': c('icono').text,
            'color': '${widget.initial?['color'] ?? '#7767F5'}',
            'orden': widget.initial?['orden'] ?? 0,
            'activa': widget.initial?['activa'] ?? true,
          };
          if (widget.initial == null) {
            await _api.crearCategoria(body);
          } else {
            await _api.actualizar(
                'categorias', widget.initial!['id'] as int, body);
          }
          break;
        case 'movimientos':
          if (widget.initial == null) {
            await _api.crearMovimiento(
                fecha: DateTime.parse(c('fecha').text),
                descripcion: c('nombre').text,
                valor: number('valor'),
                cuentaId: _account!,
                categoriaId: _category!,
                observaciones: c('nota').text);
          } else {
            await _api.actualizar('movimientos', widget.initial!['id'] as int, {
              'fecha': c('fecha').text,
              'descripcion': c('nombre').text,
              'valor': number('valor'),
              'cuenta_id': _account,
              'categoria_id': _category,
              'observaciones': c('nota').text,
            });
          }
          break;
        case 'gastos-recurrentes':
          final body = {
            'nombre': c('nombre').text,
            'valor': number('valor'),
            'frecuencia': _frequency,
            'proxima_fecha_pago': c('fecha').text,
            'categoria_id': _category,
            'activa': widget.initial?['activa'] ?? true,
          };
          if (widget.initial == null) {
            await _api.crearRecurrente(body);
          } else {
            await _api.actualizar(
                'gastos-recurrentes', widget.initial!['id'] as int, body);
          }
          break;
        case 'transferencias':
          await _api.crearTransferencia({
            'fecha': c('fecha').text,
            'cuenta_origen_id': _account,
            'cuenta_destino_id': _destination,
            'valor': number('valor'),
            'descripcion': c('nota').text
          });
          break;
        case 'presupuestos':
          final now = DateTime.now();
          await _api.crearPresupuesto({
            'anio': now.year,
            'mes': now.month,
            'categoria_id': _category,
            'valor': number('valor')
          });
          break;
        case 'metas':
          await _api.crearMeta({
            'nombre': c('nombre').text,
            'objetivo': number('valor'),
            'moneda': _currency,
            'fecha_limite': c('fecha').text,
            'descripcion': c('nota').text
          });
          break;
        case 'inversiones':
          final body = {
            'activo': c('nombre').text,
            'tipo': c('tipo').text,
            'cantidad': number('cantidad'),
            'precio_compra': number('compra'),
            'precio_actual': number('actual'),
            'broker': c('nota').text,
            'moneda': _currency,
            'valores_totales': false,
            'fecha_apertura': c('fecha').text,
            'es_posicion_inicial': _initialPosition,
            'cuenta_origen_id': _initialPosition ? null : _account
          };
          if (widget.initial == null) {
            await _api.crearInversion(body);
          } else {
            await _api.actualizar(
                'inversiones', widget.initial!['id'] as int, body);
          }
          break;
        case 'tarjetas':
          await _api.crearTarjeta({
            'nombre': c('nombre').text,
            'banco': c('nota').text,
            'ultimos_cuatro': c('ultimos').text,
            'tipo': _type == 'Crédito' ? 'Credito' : 'Debito',
            'moneda': _currency,
            'cuenta_id': _type == 'Crédito' ? null : _account
          });
          break;
      }
      if (mounted) Navigator.pop(context, true);
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(
          title: Text(
              '${widget.initial == null ? 'Nuevo' : 'Editar'} · ${widget.title}')),
      body: FinanceAurora(
          child: SafeArea(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : Form(
                      key: _form,
                      child: ListView(
                          padding: const EdgeInsets.all(18),
                          children: [
                            FinanceSurface(
                                child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.stretch,
                                    children: [
                                  Text(
                                      '${widget.initial == null ? 'Crear' : 'Editar'} ${widget.title.toLowerCase()}',
                                      style: const TextStyle(
                                          fontSize: 23,
                                          fontWeight: FontWeight.w900)),
                                  const SizedBox(height: 6),
                                  const Text(
                                      'Revisa los datos antes de guardar. El cambio se sincronizará con la web.',
                                      style: TextStyle(
                                          color: FinanceColors.muted)),
                                  const SizedBox(height: 20),
                                  ..._fields(),
                                  if (_error != null)
                                    Text(_error!,
                                        style: const TextStyle(
                                            color: FinanceColors.danger)),
                                  const SizedBox(height: 8),
                                  FilledButton.icon(
                                      onPressed: _busy ? null : _save,
                                      icon: const Icon(Icons.check_rounded),
                                      label: Text(
                                          _busy ? 'Guardando…' : 'Guardar'))
                                ]))
                          ])))));
  @override
  void dispose() {
    for (final value in _values.values) {
      value.dispose();
    }
    super.dispose();
  }
}
