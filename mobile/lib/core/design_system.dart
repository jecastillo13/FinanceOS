import 'package:flutter/material.dart';

abstract final class FinanceColors {
  static const background = Color(0xFF080D1B);
  static const surface = Color(0xFF131C32);
  static const surfaceHigh = Color(0xFF1A2746);
  static const primary = Color(0xFF7C83FF);
  static const cyan = Color(0xFF35B8F4);
  static const success = Color(0xFF35D6B4);
  static const danger = Color(0xFFFA7185);
  static const text = Color(0xFFF6F8FF);
  static const muted = Color(0xFF95A5C3);
  static const border = Color(0xFF2A3B61);
}

abstract final class FinanceTheme {
  static ThemeData get dark {
    final scheme = ColorScheme.fromSeed(
            seedColor: FinanceColors.primary, brightness: Brightness.dark)
        .copyWith(
      surface: FinanceColors.surface,
      primary: FinanceColors.primary,
      secondary: FinanceColors.cyan,
      error: FinanceColors.danger,
    );
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: scheme,
      scaffoldBackgroundColor: FinanceColors.background,
      appBarTheme: const AppBarTheme(
          backgroundColor: Colors.transparent,
          elevation: 0,
          surfaceTintColor: Colors.transparent),
      cardTheme: CardThemeData(
          color: FinanceColors.surface,
          elevation: 0,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(24))),
      textTheme: const TextTheme(
        headlineMedium: TextStyle(
            color: FinanceColors.text,
            fontSize: 29,
            height: 1.1,
            fontWeight: FontWeight.w800,
            letterSpacing: -.8),
        titleLarge: TextStyle(
            color: FinanceColors.text,
            fontSize: 20,
            fontWeight: FontWeight.w800,
            letterSpacing: -.3),
        bodyMedium:
            TextStyle(color: FinanceColors.muted, fontSize: 14, height: 1.45),
      ),
    );
  }
}

class FinanceAurora extends StatefulWidget {
  const FinanceAurora({super.key, required this.child});
  final Widget child;

  @override
  State<FinanceAurora> createState() => _FinanceAuroraState();
}

class _FinanceAuroraState extends State<FinanceAurora>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller =
      AnimationController(vsync: this, duration: const Duration(seconds: 22));

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.disableAnimationsOf(context)) {
      _controller.stop();
      _controller.value = .35;
    } else if (!_controller.isAnimating) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => RepaintBoundary(
        child: AnimatedBuilder(
          animation: _controller,
          child: widget.child,
          builder: (context, child) {
            final value = Curves.easeInOut.transform(_controller.value);
            return DecoratedBox(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  center: Alignment(-.70 + value * 1.35, -.92 + value * .48),
                  radius: 1.28,
                  colors: const [
                    Color(0xC13B63D7),
                    Color(0x88253E84),
                    FinanceColors.background
                  ],
                  stops: const [0, .36, 1],
                ),
              ),
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: RadialGradient(
                    center: Alignment(.85 - value * .40, .90 - value * .28),
                    radius: .85,
                    colors: const [Color(0x4935D6B4), Color(0x00131C32)],
                  ),
                ),
                child: child,
              ),
            );
          },
        ),
      );
}

class FinanceSurface extends StatelessWidget {
  const FinanceSurface(
      {super.key,
      required this.child,
      this.padding = const EdgeInsets.all(18),
      this.accent});
  final Widget child;
  final EdgeInsets padding;
  final Color? accent;

  @override
  Widget build(BuildContext context) => Container(
        padding: padding,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
              color: (accent ?? FinanceColors.border).withValues(alpha: .60)),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              (accent ?? FinanceColors.surfaceHigh).withValues(alpha: .32),
              FinanceColors.surface.withValues(alpha: .94)
            ],
          ),
          boxShadow: const [
            BoxShadow(
                color: Color(0x33000000), blurRadius: 30, offset: Offset(0, 14))
          ],
        ),
        child: child,
      );
}
