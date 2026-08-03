import 'dart:convert';

import 'package:http/http.dart' as http;

/// En Android físico usa la IP privada de tu computador:
/// --dart-define=API_URL=http://192.168.1.5:8000
const apiBaseUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Future<Map<String, dynamic>> resumenDashboard() => _getObject('/api/v1/dashboard/resumen');

  Future<List<dynamic>> cuentas() => _getList('/api/v1/cuentas');

  Future<List<dynamic>> metas() => _getList('/api/v1/metas');

  Future<Map<String, dynamic>> aportarMeta({
    required int metaId,
    required double valor,
    required DateTime fecha,
    String descripcion = '',
  }) => _postObject('/api/v1/metas/$metaId/aportes', {
        'valor': valor,
        'fecha': _fecha(fecha),
        'descripcion': descripcion,
      });

  Future<Map<String, dynamic>> pagarMeta({
    required int metaId,
    required double valor,
    required DateTime fecha,
    required int cuentaId,
    required int categoriaId,
    required String descripcion,
    String observaciones = '',
  }) => _postObject('/api/v1/metas/$metaId/pagos', {
        'valor': valor,
        'fecha': _fecha(fecha),
        'cuenta_id': cuentaId,
        'categoria_id': categoriaId,
        'descripcion': descripcion,
        'observaciones': observaciones,
      });

  Future<Map<String, dynamic>> adjuntarComprobante({
    required int movimientoId,
    required String rutaArchivo,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$apiBaseUrl/api/v1/movimientos/$movimientoId/comprobantes'),
    );
    request.files.add(await http.MultipartFile.fromPath('archivo', rutaArchivo));
    final response = await http.Response.fromStream(await request.send());
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _getObject(String path) async {
    final response = await _client.get(Uri.parse('$apiBaseUrl$path'));
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _getList(String path) async {
    final response = await _client.get(Uri.parse('$apiBaseUrl$path'));
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> _postObject(String path, Map<String, dynamic> body) async {
    final response = await _client.post(
      Uri.parse('$apiBaseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  String _fecha(DateTime value) => value.toIso8601String().split('T').first;
}

class ApiException implements Exception {
  const ApiException(this.statusCode, this.body);
  final int statusCode;
  final String body;
}
