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

  static String? sessionToken;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (sessionToken != null) 'Authorization': 'Bearer $sessionToken',
      };

  Future<Map<String, dynamic>> login(String correo, String password,
          {String? mfaCodigo}) =>
      _postObject('/api/v1/auth/mobile/login', {
        'correo': correo,
        'password': password,
        if (mfaCodigo?.isNotEmpty == true) 'mfa_codigo': mfaCodigo
      });

  Future<Map<String, dynamic>> authStatus() =>
      _getObject('/api/v1/auth/status');
  Future<Map<String, dynamic>> prepararMfa() =>
      _postObject('/api/v1/auth/mfa/preparar', {});
  Future<Map<String, dynamic>> confirmarMfa(String codigo) =>
      _postObject('/api/v1/auth/mfa/confirmar', {'codigo': codigo});
  Future<List<dynamic>> usuarios() => _getList('/api/v1/auth/usuarios');
  Future<List<dynamic>> sesiones() => _getList('/api/v1/auth/sesiones');
  Future<void> revocarSesion(int id) => _delete('/api/v1/auth/sesiones/$id');
  Future<Map<String, dynamic>> crearUsuario(Map<String, dynamic> body) =>
      _postObject('/api/v1/auth/usuarios', body);
  Future<void> logout() async {
    await _postObject('/api/v1/auth/logout', {});
    sessionToken = null;
  }

  Future<Map<String, dynamic>> resumenDashboard() =>
      _getObject('/api/v1/dashboard/resumen');

  Future<Map<String, dynamic>> graficasDashboard() =>
      _getObject('/api/v1/dashboard/graficas');

  Future<List<dynamic>> cuentas() => _getList('/api/v1/cuentas');

  Future<List<dynamic>> metas() => _getList('/api/v1/metas');

  Future<List<dynamic>> tarjetas() => _getList('/api/v1/tarjetas');

  Future<List<dynamic>> detecciones() =>
      _getList('/api/v1/detecciones?estado=Pendiente');

  Future<List<dynamic>> categorias() => _getList('/api/v1/categorias');

  Future<List<dynamic>> movimientos() =>
      _getList('/api/v1/movimientos?limite=100');
  Future<List<dynamic>> recurrentes() => _getList('/api/v1/gastos-recurrentes');
  Future<List<dynamic>> transferencias() => _getList('/api/v1/transferencias');
  Future<List<dynamic>> presupuestos({required int anio, required int mes}) =>
      _getList('/api/v1/presupuestos?anio=$anio&mes=$mes');
  Future<Map<String, dynamic>> inversiones() =>
      _getObject('/api/v1/inversiones');
  Future<List<dynamic>> tasas() => _getList('/api/v1/monedas/tasas');
  Future<Map<String, dynamic>> reporte({required int anio, required int mes}) =>
      _getObject('/api/v1/reportes/$anio/$mes/resumen');
  Future<Map<String, dynamic>> estadoRespaldo() =>
      _getObject('/api/v1/configuracion/respaldo');

  Future<Map<String, dynamic>> crearCuenta(Map<String, dynamic> body) =>
      _postObject('/api/v1/cuentas', body);
  Future<Map<String, dynamic>> crearCategoria(Map<String, dynamic> body) =>
      _postObject('/api/v1/categorias', body);
  Future<Map<String, dynamic>> crearMeta(Map<String, dynamic> body) =>
      _postObject('/api/v1/metas', body);
  Future<Map<String, dynamic>> crearRecurrente(Map<String, dynamic> body) =>
      _postObject('/api/v1/gastos-recurrentes', body);
  Future<Map<String, dynamic>> crearTransferencia(Map<String, dynamic> body) =>
      _postObject('/api/v1/transferencias', body);
  Future<Map<String, dynamic>> crearPresupuesto(Map<String, dynamic> body) =>
      _postObject('/api/v1/presupuestos', body);
  Future<Map<String, dynamic>> crearInversion(Map<String, dynamic> body) =>
      _postObject('/api/v1/inversiones', body);
  Future<Map<String, dynamic>> crearTarjeta(Map<String, dynamic> body) =>
      _postObject('/api/v1/tarjetas', body);
  Future<Map<String, dynamic>> pagarRecurrente(int id, int cuentaId) =>
      _postObject('/api/v1/gastos-recurrentes/$id/pagar',
          {'cuenta_id': cuentaId, 'fecha_pago': _fecha(DateTime.now())});
  Future<Map<String, dynamic>> pagarTarjeta(
          int id, int cuentaId, double valor) =>
      _postObject('/api/v1/tarjetas/$id/pagar', {
        'cuenta_origen_id': cuentaId,
        'valor': valor,
        'fecha': _fecha(DateTime.now()),
        'descripcion': 'Pago desde FinanceOS Mobile'
      });
  Future<Map<String, dynamic>> actualizarTasas() =>
      _postObject('/api/v1/monedas/tasas/actualizar', {});

  Future<void> eliminar(String recurso, int id) =>
      _delete('/api/v1/$recurso/$id');
  Future<Map<String, dynamic>> actualizar(
          String recurso, int id, Map<String, dynamic> body) =>
      _putObject('/api/v1/$recurso/$id', body);

  Future<Map<String, dynamic>> crearMovimiento({
    required DateTime fecha,
    required String descripcion,
    required double valor,
    required int cuentaId,
    required int categoriaId,
    String observaciones = '',
    String? huella,
  }) =>
      _postObject('/api/v1/movimientos', {
        'fecha': _fecha(fecha),
        'descripcion': descripcion,
        'valor': valor,
        'cuenta_id': cuentaId,
        'categoria_id': categoriaId,
        'observaciones': observaciones,
        if (huella != null) 'huella': huella,
      });

  Future<Map<String, dynamic>> detectarOperacion(String texto,
          {String origen = 'Movil'}) =>
      _postObject('/api/v1/detecciones', {'texto': texto, 'origen': origen});

  Future<Map<String, dynamic>> confirmarDeteccion({
    required int deteccionId,
    required int categoriaId,
    int? tarjetaId,
    int? cuentaId,
  }) =>
      _postObject('/api/v1/detecciones/$deteccionId/confirmar', {
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
  }) =>
      _postObject('/api/v1/metas/$metaId/aportes', {
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
  }) =>
      _postObject('/api/v1/metas/$metaId/pagos', {
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
    if (sessionToken != null) {
      request.headers['Authorization'] = 'Bearer $sessionToken';
    }
    request.files
        .add(await http.MultipartFile.fromPath('archivo', rutaArchivo));
    final response = await http.Response.fromStream(await request.send());
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _getObject(String path) async {
    final response =
        await _client.get(Uri.parse('$apiBaseUrl$path'), headers: _headers);
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _getList(String path) async {
    final response =
        await _client.get(Uri.parse('$apiBaseUrl$path'), headers: _headers);
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> _postObject(
      String path, Map<String, dynamic> body) async {
    final response = await _client.post(
      Uri.parse('$apiBaseUrl$path'),
      headers: _headers,
      body: jsonEncode(body),
    );
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _putObject(
      String path, Map<String, dynamic> body) async {
    final response = await _client.put(Uri.parse('$apiBaseUrl$path'),
        headers: _headers, body: jsonEncode(body));
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> _delete(String path) async {
    final response =
        await _client.delete(Uri.parse('$apiBaseUrl$path'), headers: _headers);
    if (response.statusCode >= 400) {
      throw ApiException(response.statusCode, response.body);
    }
  }

  String _fecha(DateTime value) => value.toIso8601String().split('T').first;
}

class ApiException implements Exception {
  const ApiException(this.statusCode, this.body);
  final int statusCode;
  final String body;
  @override
  String toString() {
    try {
      final value = jsonDecode(body);
      return '${value['detail'] ?? body}';
    } catch (_) {
      return body;
    }
  }
}
