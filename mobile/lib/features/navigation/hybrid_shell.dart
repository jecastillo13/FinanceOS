import 'package:file_picker/file_picker.dart' as native_picker;
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';

import '../../core/design_system.dart';

const financeWebUrl = String.fromEnvironment('WEB_URL', defaultValue: 'http://10.0.2.2:8000');

/// Contenedor híbrido: React comparte interfaz y funciones con la web,
/// mientras Flutter conserva capacidades nativas como cámara y OCR.
class HybridShell extends StatefulWidget {
  const HybridShell({super.key});
  @override State<HybridShell> createState()=>_HybridShellState();
}

class _HybridShellState extends State<HybridShell>{
  late final WebViewController _controller;
  final ImagePicker _imagePicker = ImagePicker();
  int _progress=0; String? _error;

  @override void initState(){super.initState();_controller=WebViewController()
    ..setJavaScriptMode(JavaScriptMode.unrestricted)
    ..setBackgroundColor(FinanceColors.background)
    ..setNavigationDelegate(NavigationDelegate(
      onProgress:(value)=>setState(()=>_progress=value),
      onPageFinished:(_)=>setState((){_progress=100;_error=null;}),
      onWebResourceError:(error){if(error.isForMainFrame==true)setState(()=>_error=error.description);},
    ));
    final platformController = _controller.platform;
    if (platformController is AndroidWebViewController) {
      platformController.setOnShowFileSelector(_selectFiles);
    }
    _controller.loadRequest(Uri.parse(financeWebUrl));}

  Future<List<String>> _selectFiles(FileSelectorParams params) async {
    if (params.isCaptureEnabled) {
      final photo = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 90,
      );
      return photo == null ? <String>[] : <String>[Uri.file(photo.path).toString()];
    }

    const extensions = <String>['pdf', 'png', 'jpg', 'jpeg', 'webp'];
    final List<native_picker.PlatformFile> files;
    if (params.mode == FileSelectorMode.openMultiple) {
      files = await native_picker.FilePicker.pickFiles(
        type: native_picker.FileType.custom,
        allowedExtensions: extensions,
      );
    } else {
      final file = await native_picker.FilePicker.pickFile(
        type: native_picker.FileType.custom,
        allowedExtensions: extensions,
      );
      files = file == null ? <native_picker.PlatformFile>[] : <native_picker.PlatformFile>[file];
    }
    return files
        .where((file) => file.path != null)
        .map((file) => Uri.file(file.path!).toString())
        .toList();
  }

  Widget _errorView()=>Positioned.fill(
    child:ColoredBox(
      color:FinanceColors.background,
      child:Center(
        child:Padding(
          padding:const EdgeInsets.all(28),
          child:FinanceSurface(
            child:Column(mainAxisSize:MainAxisSize.min,children:[
              const Icon(Icons.cloud_off_rounded,size:52,color:FinanceColors.danger),
              const SizedBox(height:16),
              const Text('No pudimos abrir FinanceOS',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900)),
              const SizedBox(height:8),
              Text(_error!,textAlign:TextAlign.center,style:const TextStyle(color:FinanceColors.muted)),
              const SizedBox(height:18),
              FilledButton.icon(onPressed:(){setState(()=>_error=null);_controller.reload();},icon:const Icon(Icons.refresh_rounded),label:const Text('Reintentar')),
            ]),
          ),
        ),
      ),
    ),
  );

  @override Widget build(BuildContext context)=>Scaffold(
    backgroundColor:FinanceColors.background,
    body:SafeArea(bottom:false,child:Stack(children:[
      WebViewWidget(controller:_controller),
      if(_progress<100)LinearProgressIndicator(value:_progress/100,color:FinanceColors.cyan,backgroundColor:Colors.transparent),
      if(_error!=null)_errorView(),
    ])),
  );
}
