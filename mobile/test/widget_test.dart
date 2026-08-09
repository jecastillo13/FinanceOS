import 'package:flutter_test/flutter_test.dart';

import 'package:financeos_mobile/main.dart';

void main() {
  test('FinanceOS expone la aplicacion movil principal', () {
    expect(const FinanceOSMobile(), isA<FinanceOSMobile>());
  });
}
