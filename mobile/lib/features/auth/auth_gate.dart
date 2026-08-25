import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/api_client.dart';
import '../../core/design_system.dart';
import '../navigation/mobile_shell.dart';

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});
  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );
  final _api = ApiClient();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _mfa = TextEditingController();
  bool _loading = true,
      _authenticated = false,
      _busy = false,
      _needsMfa = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final token = await _storage.read(key: 'financeos_session');
    if (token != null) {
      ApiClient.sessionToken = token;
      try {
        final state = await _api.authStatus();
        if (state['autenticado'] == true) {
          if (mounted) setState(() => _authenticated = true);
        }
      } catch (_) {
        await _storage.delete(key: 'financeos_session');
        ApiClient.sessionToken = null;
      }
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _login() async {
    if (_email.text.trim().isEmpty || _password.text.isEmpty) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final result = await _api.login(_email.text.trim(), _password.text,
          mfaCodigo: _mfa.text.trim());
      final token = '${result['token']}';
      ApiClient.sessionToken = token;
      await _storage.write(key: 'financeos_session', value: token);
      if (mounted) setState(() => _authenticated = true);
    } on ApiException catch (error) {
      final text = error.toString();
      setState(() {
        _error = text;
        _needsMfa = text.toLowerCase().contains('mfa') ||
            text.toLowerCase().contains('código');
      });
    } catch (error) {
      setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _logout() async {
    try {
      await _api.logout();
    } catch (_) {}
    await _storage.delete(key: 'financeos_session');
    if (mounted) {
      setState(() {
        _authenticated = false;
        _needsMfa = false;
        _password.clear();
        _mfa.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (_authenticated) return MobileShell(onLogout: _logout);
    return Scaffold(
      body: FinanceAurora(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(22),
              child: FinanceSurface(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const CircleAvatar(
                        radius: 30,
                        backgroundColor: FinanceColors.primary,
                        child: Icon(Icons.account_balance_wallet_rounded,
                            color: Colors.white, size: 30)),
                    const SizedBox(height: 18),
                    const Text('Bienvenido a FinanceOS',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                            fontSize: 26, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 7),
                    const Text(
                        'Inicia sesión en tu espacio privado. La web y el celular utilizan exactamente los mismos datos.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: FinanceColors.muted)),
                    const SizedBox(height: 22),
                    TextField(
                        controller: _email,
                        keyboardType: TextInputType.emailAddress,
                        autofillHints: const [AutofillHints.email],
                        decoration: const InputDecoration(
                            labelText: 'Correo',
                            prefixIcon: Icon(Icons.alternate_email_rounded))),
                    const SizedBox(height: 12),
                    TextField(
                        controller: _password,
                        obscureText: true,
                        autofillHints: const [AutofillHints.password],
                        decoration: const InputDecoration(
                            labelText: 'Contraseña',
                            prefixIcon: Icon(Icons.lock_rounded))),
                    if (_needsMfa) ...[
                      const SizedBox(height: 12),
                      TextField(
                          controller: _mfa,
                          keyboardType: TextInputType.number,
                          maxLength: 6,
                          decoration: const InputDecoration(
                              labelText: 'Código MFA',
                              prefixIcon: Icon(Icons.shield_rounded))),
                    ],
                    if (_error != null)
                      Padding(
                          padding: const EdgeInsets.only(top: 12),
                          child: Text(_error!,
                              style: const TextStyle(
                                  color: FinanceColors.danger))),
                    const SizedBox(height: 18),
                    FilledButton.icon(
                        onPressed: _busy ? null : _login,
                        icon: _busy
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(Icons.login_rounded),
                        label: Text(
                            _busy ? 'Verificando…' : 'Entrar de forma segura')),
                    const SizedBox(height: 14),
                    const Row(children: [
                      Icon(Icons.verified_user_rounded,
                          color: FinanceColors.success, size: 18),
                      SizedBox(width: 8),
                      Expanded(
                          child: Text(
                              'La sesión se guarda cifrada en Android Keystore o iOS Keychain.',
                              style: TextStyle(
                                  color: FinanceColors.muted, fontSize: 12)))
                    ]),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _mfa.dispose();
    super.dispose();
  }
}
