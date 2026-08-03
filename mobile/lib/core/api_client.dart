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
}

class ApiException implements Exception {
  const ApiException(this.statusCode, this.body);
  final int statusCode;
  final String body;
}
