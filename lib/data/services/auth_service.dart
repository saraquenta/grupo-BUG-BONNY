import '../models/user_model.dart';
import 'api_service.dart';
import '../../core/constants/api_constants.dart';

class AuthService {
  AuthService._();

 
  static Future<AuthResponse> login(String username, String password) async {
    final data = await ApiService.postForm(
      ApiConstants.login,
      {'username': username, 'password': password},
    );
    return AuthResponse.fromJson(data as Map<String, dynamic>);
  }

  static Future<UserModel> getMe() async {
    final data = await ApiService.get(ApiConstants.me);
    return UserModel.fromJson(data as Map<String, dynamic>);
  }
}
