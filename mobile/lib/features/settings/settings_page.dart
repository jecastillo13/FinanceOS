import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../core/design_system.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});
  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _api = ApiClient();
  late Future<List<dynamic>> users = load();
  String? message;
  Future<List<dynamic>> load() async {
    try {
      return await _api.usuarios();
    } catch (_) {
      return [];
    }
  }

  Future<void> activateMfa() async {
    try {
      final setup = await _api.prepararMfa();
      if (!mounted) return;
      final code = TextEditingController();
      final accepted = await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
                title: const Text('Activar MFA'),
                content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Copia esta clave en tu autenticador:'),
                      const SizedBox(height: 10),
                      SelectableText('${setup['secreto']}',
                          style: const TextStyle(
                              fontWeight: FontWeight.w900,
                              color: FinanceColors.cyan)),
                      const SizedBox(height: 12),
                      TextField(
                          controller: code,
                          keyboardType: TextInputType.number,
                          maxLength: 6,
                          decoration: const InputDecoration(
                              labelText: 'Código de seis dígitos'))
                    ]),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () async {
                        try {
                          await _api.confirmarMfa(code.text);
                          if (context.mounted) Navigator.pop(context, true);
                        } catch (error) {
                          if (context.mounted)
                            ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('$error')));
                        }
                      },
                      child: const Text('Confirmar'))
                ],
              ));
      code.dispose();
      if (accepted == true)
        setState(() => message = 'MFA activado correctamente.');
    } catch (error) {
      setState(() => message = '$error');
    }
  }

  Future<void> createUser() async {
    final name = TextEditingController(),
        email = TextEditingController(),
        password = TextEditingController();
    final saved = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
              title: const Text('Crear usuario privado'),
              content: Column(mainAxisSize: MainAxisSize.min, children: [
                TextField(
                    controller: name,
                    decoration: const InputDecoration(labelText: 'Nombre')),
                const SizedBox(height: 10),
                TextField(
                    controller: email,
                    decoration: const InputDecoration(labelText: 'Correo')),
                const SizedBox(height: 10),
                TextField(
                    controller: password,
                    obscureText: true,
                    decoration: const InputDecoration(
                        labelText: 'Contraseña temporal (12+)'))
              ]),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    onPressed: () async {
                      try {
                        await _api.crearUsuario({
                          'nombre': name.text,
                          'correo': email.text,
                          'password': password.text
                        });
                        if (context.mounted) Navigator.pop(context, true);
                      } catch (error) {
                        if (context.mounted)
                          ScaffoldMessenger.of(context)
                              .showSnackBar(SnackBar(content: Text('$error')));
                      }
                    },
                    child: const Text('Crear'))
              ],
            ));
    name.dispose();
    email.dispose();
    password.dispose();
    if (saved == true) setState(() => users = load());
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Configuración')),
        body: FinanceAurora(
            child: SafeArea(
                child: FutureBuilder<List<dynamic>>(
          future: users,
          builder: (context, snapshot) =>
              ListView(padding: const EdgeInsets.all(18), children: [
            FinanceSurface(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                  const Text('Seguridad y acceso',
                      style:
                          TextStyle(fontSize: 23, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 8),
                  const Text(
                      'Protege tu cuenta y administra personas sin mezclar información financiera.',
                      style: TextStyle(color: FinanceColors.muted)),
                  const SizedBox(height: 18),
                  FilledButton.icon(
                      onPressed: activateMfa,
                      icon: const Icon(Icons.shield_rounded),
                      label: const Text('Activar autenticación MFA')),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                      onPressed: createUser,
                      icon: const Icon(Icons.person_add_alt_1_rounded),
                      label: const Text('Crear usuario')),
                  if (message != null)
                    Padding(
                        padding: const EdgeInsets.only(top: 12),
                        child: Text(message!,
                            style:
                                const TextStyle(color: FinanceColors.success)))
                ])),
            const SizedBox(height: 16),
            FinanceSurface(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                  Text('Usuarios (${snapshot.data?.length ?? 0})',
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 10),
                  ...(snapshot.data ?? []).map((u) => ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading:
                          const CircleAvatar(child: Icon(Icons.person_rounded)),
                      title: Text('${u['nombre']}'),
                      subtitle: Text('${u['correo']}'),
                      trailing: Text('${u['rol']}')))
                ])),
          ]),
        ))),
      );
}
