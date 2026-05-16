import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/constants/app_strings.dart';
import '../../../core/utils/validators.dart';
import '../../../providers/auth_provider.dart';
import '../../widgets/custom_button.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey      = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool  _obscurePass  = true;

  @override
  void dispose() {
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;

    final auth    = context.read<AuthProvider>();
    final success = await auth.login(
      _usernameCtrl.text,
      _passwordCtrl.text,
    );

    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.errorMsg ?? AppStrings.loginError),
          backgroundColor: AppColors.danger,
          behavior:        SnackBarBehavior.floating,
          margin: const EdgeInsets.all(16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth      = context.watch<AuthProvider>();
    final size      = MediaQuery.of(context).size;
    final topHeight = size.height * 0.38;

    return Scaffold(
      body: SingleChildScrollView(
        child: SizedBox(
          height: size.height,
          child: Column(
            children: [
              _buildHeader(topHeight),

              Expanded(
                child: Container(
                  decoration: const BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.only(
                      topLeft:  Radius.circular(32),
                      topRight: Radius.circular(32),
                    ),
                  ),
                  padding: const EdgeInsets.fromLTRB(28, 32, 28, 24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Título
                        const Text(
                          AppStrings.login,
                          style: TextStyle(
                            fontSize:   26,
                            fontWeight: FontWeight.bold,
                            color:      AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          AppStrings.loginSubtitle,
                          style: TextStyle(
                            color:    AppColors.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 28),

                        TextFormField(
                          controller:        _usernameCtrl,
                          textInputAction:   TextInputAction.next,
                          autocorrect:       false,
                          validator:         Validators.username,
                          decoration: const InputDecoration(
                            labelText:   AppStrings.username,
                            hintText:    AppStrings.usernamehint,
                            prefixIcon:  Icon(Icons.person_outline_rounded),
                          ),
                        ),
                        const SizedBox(height: 16),

                        TextFormField(
                          controller:      _passwordCtrl,
                          obscureText:     _obscurePass,
                          textInputAction: TextInputAction.done,
                          onFieldSubmitted:(_) => _handleLogin(),
                          validator:       Validators.password,
                          decoration: InputDecoration(
                            labelText:  AppStrings.password,
                            hintText:   AppStrings.passwordHint,
                            prefixIcon: const Icon(Icons.lock_outline_rounded),
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscurePass
                                    ? Icons.visibility_off_outlined
                                    : Icons.visibility_outlined,
                                color: AppColors.textSecondary,
                              ),
                              onPressed: () =>
                                  setState(() => _obscurePass = !_obscurePass),
                            ),
                          ),
                        ),
                        const SizedBox(height: 32),

                        CustomButton(
                          label:     AppStrings.loginButton,
                          isLoading: auth.isLoading,
                          onPressed: _handleLogin,
                          icon:      Icons.login_rounded,
                        ),

                        const Spacer(),

                        Center(
                          child: Text(
                            '${AppStrings.version} — ${AppStrings.university}',
                            style: const TextStyle(
                              color:    AppColors.textHint,
                              fontSize: 11,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(double height) {
    return Container(
      height: height,
      width:  double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.primaryDark, AppColors.primary],
          begin:  Alignment.topCenter,
          end:    Alignment.bottomCenter,
        ),
      ),
      child: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Container(
              width:  86,
              height: 86,
              decoration: BoxDecoration(
                color:        Colors.white,
                borderRadius: BorderRadius.circular(22),
                boxShadow: [
                  BoxShadow(
                    color:     Colors.black.withOpacity(0.2),
                    blurRadius: 16,
                    offset:    const Offset(0, 6),
                  ),
                ],
              ),
              child: const Icon(
                Icons.medical_services_rounded,
                size:  50,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              AppStrings.appName,
              style: TextStyle(
                color:      Colors.white,
                fontSize:   28,
                fontWeight: FontWeight.bold,
                letterSpacing: 1.2,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              AppStrings.company,
              style: TextStyle(
                color:    Colors.white70,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
