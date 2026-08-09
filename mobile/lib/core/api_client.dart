import 'dart:convert';

import 'package:http/http.dart' as http;

/// En Android físico usa la IP privada de tu computador:
/// --dart-define=API_URL=http://192.168.1.5:8000
const apiBaseUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);
const apiToken = String.fromEnvironment('API_TOKEN', defaultValue: '');

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (apiToken.isNotEmpty) 'Authorization': 'Bearer $apiToken',
      };

  Future<Map<String, dynamic>> resumenDashboard() => _getObject('/api/v1/dashboard/resumen');

  Future<Map<String, dynamic>> graficasDashboard() => _getObject('/api/v1/dashboard/graficas');

  Future<List<dynamic>> cuentas() => _getList('/api/v1/cuentas');

  Future<List<dynamic>> metas() => _getList('/api/v1/metas');

  Future<List<dynamic>> tarjetas() => _getList('/api/v1/tarjetas');

  Future<List<dynamic>> detecciones() => _getList('/api/v1/detecciones?estado=Pendiente');

  Future<List<dynamic>> categorias() => _getList('/api/v1/categorias');

  Future<Map<String, dynamic>> crearMovimiento({
    required DateTime fecha,
    required String descripcion,
    required double valor,
    required int cuentaId,
    required int categoriaId,
    String observaciones = '',
    String? huella,
  }) => _postObject('/api/v1/movimientos', {
        'fecha': _fecha(fecha),
        'descripcion': descripcion,
        'valor': valor,
        'cuenta_id': cuentaId,
        'categoria_id': categoriaId,
        'observaciones': observaciones,
        if (huella != null) 'huella': huella,
      });

  Future<Map<String, dynamic>> detectarOperacion(String texto, {String origen = 'Movil'}) =>
      _postObject('/api/v1/detecciones', {'texto': texto, 'origen': origen});

  Future<Map<String, dynamic>> confirmarDeteccion({
    required int deteccionId,
    required int categoriaId,
    int? tarjetaId,
    int? cuentaId,
  }) => _postObject('/api/v1/detecciones/$deteccionId/confirmar', {
        'categoria_id': categoriaId,
        'tarjeta_id': tarjetaId,
        'cuenta_id': cuentaId,
      });

  Future<Map<String, dynamic>> descartarDeteccion(int deteccionId) =>
      _postObject('/api/v1/detecciones/$deteccionId/descartar', {});

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
    if (apiToken.isNotEmpty) request.headers['Authorization'] = 'Bearer $apiToken';
    request.files.add(await http.MultipartFile.fromPath('archivo', rutaArchivo));
    final response = await http.Response.fromStream(await request.send());
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _getObject(String path) async {
    final response = await _client.get(Uri.parse('$apiBaseUrl$path'), headers: _headers);
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _getList(String path) async {
    final response = await _client.get(Uri.parse('$apiBaseUrl$path'), headers: _headers);
    if (response.statusCode >= 400) throw ApiException(response.statusCode, response.body);
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> _postObject(String path, Map<String, dynamic> body) async {
    final response = await _client.post(
      Uri.parse('$apiBaseUrl$path'),
      headers: _headers,
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
