import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';

class ReceiptScanPage extends StatefulWidget {
  const ReceiptScanPage({super.key});

  @override
  State<ReceiptScanPage> createState() => _ReceiptScanPageState();
}

class _ReceiptScanPageState extends State<ReceiptScanPage> {
  final _api = ApiClient();
  final _picker = ImagePicker();
  final _description = TextEditingController();
  final _value = TextEditingController();
  XFile? _photo;
  List<dynamic> _accounts = const [];
  List<dynamic> _categories = const [];
  int? _accountId, _categoryId;
  bool _busy = false;
  String? _error, _fingerprint;

  @override
  void initState() {
    super.initState();
    _loadOptions();
  }

  Future<void> _loadOptions() async {
    try {
      final data = await Future.wait([_api.cuentas(), _api.categorias()]);
      if (!mounted) return;
      setState(() {
        _accounts = data[0];
        _categories = data[1].where((item) => '${item['tipo']}'.toLowerCase() == 'gasto').toList();
        _accountId = _accounts.isEmpty ? null : _accounts.first['id'] as int;
        _categoryId = _categories.isEmpty ? null : _categories.first['id'] as int;
      });
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    }
  }

  Future<void> _capture() async {
    final photo = await _picker.pickImage(source: ImageSource.camera, imageQuality: 88);
    if (photo == null) return;
    setState(() { _busy = true; _error = null; _photo = photo; });
    final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
    try {
      final result = await recognizer.processImage(InputImage.fromFilePath(photo.path));
      final text = result.text;
      final total = _extractTotal(text);
      final firstLine = text.split('\n').map((line) => line.trim()).firstWhere(
        (line) => line.length > 2 && !RegExp(r'factura|nit|total|fecha', caseSensitive: false).hasMatch(line),
        orElse: () => 'Compra con comprobante',
      );
      final stable = '${DateTime.now().toIso8601String().split('T').first}|$total|${text.toLowerCase().replaceAll(RegExp(r'\s+'), ' ').trim()}';
      setState(() {
        _description.text = firstLine.length > 120 ? firstLine.substring(0, 120) : firstLine;
        _value.text = total?.toString() ?? '';
        _fingerprint = sha256.convert(utf8.encode(stable)).toString();
      });
    } catch (error) {
      setState(() => _error = 'No fue posible leer la factura: $error');
    } finally {
      await recognizer.close();
      if (mounted) setState(() => _busy = false);
    }
  }

  double? _extractTotal(String text) {
    final normalized = text.replaceAll(RegExp(r'([\d.,])\s+(?=[\d.,])'), r'$1');
    final patterns = [
      RegExp(r'total\s*\(\s*cop\s*\)\s*:?\s*\$?\s*([\d.,]+)', caseSensitive: false),
      RegExp(r'total\s+a\s+pagar\s*:?\s*\$?\s*([\d.,]+)', caseSensitive: false),
      RegExp(r'(?:^|\n)\s*total\s*:?\s*\$?\s*([\d.,]+)', caseSensitive: false),
    ];
    for (final pattern in patterns) {
      final values = pattern.allMatches(normalized).map((match) => _number(match.group(1)!)).whereType<double>().toList();
      if (values.isNotEmpty) { values.sort(); return values.last; }
    }
    return null;
  }

  double? _number(String raw) {
    final clean = raw.replaceAll(RegExp(r'[^\d.,]'), '');
    final separator = clean.lastIndexOf(',') > clean.lastIndexOf('.') ? ',' : '.';
    final index = clean.lastIndexOf(separator);
    final decimal = index >= 0 && clean.length - index - 1 == 2;
    final normalized = decimal
        ? '${clean.substring(0, index).replaceAll(RegExp(r'[.,]'), '')}.${clean.substring(index + 1)}'
        : clean.replaceAll(RegExp(r'[.,]'), '');
    return double.tryParse(normalized);
  }

  Future<void> _save() async {
    final amount = double.tryParse(_value.text.replaceAll(',', '.'));
    if (_photo == null || amount == null || amount <= 0 || _accountId == null || _categoryId == null) return;
    setState(() { _busy = true; _error = null; });
    try {
      final movement = await _api.crearMovimiento(
        fecha: DateTime.now(), descripcion: _description.text.trim(), valor: amount,
        cuentaId: _accountId!, categoriaId: _categoryId!,
        observaciones: 'Creado desde una factura fotografiada en FinanceOS Mobile.', huella: _fingerprint,
      );
      await _api.adjuntarComprobante(movimientoId: movement['id'] as int, rutaArchivo: _photo!.path);
      if (mounted) Navigator.of(context).pop(true);
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Escanear factura')),
    body: FinanceAurora(child: SafeArea(child: ListView(padding: const EdgeInsets.all(18), children: [
      FinanceSurface(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('Captura inteligente', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
        const SizedBox(height: 7),
        const Text('Toma una foto, revisa los datos y confirma antes de afectar tu saldo.', style: TextStyle(color: FinanceColors.muted)),
        const SizedBox(height: 16),
        if (_photo != null) ClipRRect(borderRadius: BorderRadius.circular(18), child: Image.file(File(_photo!.path), height: 210, width: double.infinity, fit: BoxFit.cover)),
        const SizedBox(height: 14),
        SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _busy ? null : _capture, icon: const Icon(Icons.camera_alt_rounded), label: Text(_photo == null ? 'Abrir cámara' : 'Tomar otra foto'))),
      ])),
      if (_photo != null) ...[
        const SizedBox(height: 14),
        FinanceSurface(child: Column(children: [
          TextField(controller: _description, decoration: const InputDecoration(labelText: 'Comercio o descripción')),
          const SizedBox(height: 10),
          TextField(controller: _value, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Total')),
          const SizedBox(height: 10),
          DropdownButtonFormField<int>(value: _accountId, decoration: const InputDecoration(labelText: 'Cuenta'), items: _accounts.map((item) => DropdownMenuItem<int>(value: item['id'] as int, child: Text('${item['nombre']} (${item['moneda']})'))).toList(), onChanged: (value) => setState(() => _accountId = value)),
          const SizedBox(height: 10),
          DropdownButtonFormField<int>(value: _categoryId, decoration: const InputDecoration(labelText: 'Categoría'), items: _categories.map((item) => DropdownMenuItem<int>(value: item['id'] as int, child: Text('${item['nombre']}'))).toList(), onChanged: (value) => setState(() => _categoryId = value)),
          if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: const TextStyle(color: FinanceColors.danger))),
          const SizedBox(height: 14),
          SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _busy ? null : _save, icon: const Icon(Icons.check_rounded), label: const Text('Confirmar movimiento'))),
        ])),
      ],
    ]))),
  );

  @override
  void dispose() {
    _description.dispose();
    _value.dispose();
    super.dispose();
  }
}
