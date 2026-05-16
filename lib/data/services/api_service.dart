import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../../core/constants/api_constants.dart';
import '../services/storage_service.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiService {
  ApiService._();

  static Map<String, String> get _baseHeaders => {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  static Future<Map<String, String>> get _authHeaders async {
    final token = await StorageService.getToken();
    return {
      ..._baseHeaders,
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<dynamic> get(String endpoint) async {
    try {
      final response = await http
          .get(
            Uri.parse('${ApiConstants.baseUrl}$endpoint'),
            headers: await _authHeaders,
          )
          .timeout(ApiConstants.receiveTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Sin conexión a internet. Verifica tu red.');
    } on HttpException {
      throw ApiException('Error de conexión con el servidor.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error inesperado: $e');
    }
  }

  static Future<dynamic> post(String endpoint, Map<String, dynamic> body) async {
    try {
      final response = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}$endpoint'),
            headers: await _authHeaders,
            body: jsonEncode(body),
          )
          .timeout(ApiConstants.receiveTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Sin conexión a internet. Verifica tu red.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error inesperado: $e');
    }
  }

  static Future<dynamic> postForm(String endpoint, Map<String, String> body) async {
    try {
      final response = await http
          .post(
            Uri.parse('${ApiConstants.baseUrl}$endpoint'),
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'Accept': 'application/json',
            },
            body: body,
          )
          .timeout(ApiConstants.receiveTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Sin conexión a internet. Verifica tu red.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error inesperado: $e');
    }
  }

  static Future<dynamic> put(String endpoint, Map<String, dynamic> body) async {
    try {
      final response = await http
          .put(
            Uri.parse('${ApiConstants.baseUrl}$endpoint'),
            headers: await _authHeaders,
            body: jsonEncode(body),
          )
          .timeout(ApiConstants.receiveTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Sin conexión a internet. Verifica tu red.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error inesperado: $e');
    }
  }

  static Future<dynamic> delete(String endpoint) async {
    try {
      final response = await http
          .delete(
            Uri.parse('${ApiConstants.baseUrl}$endpoint'),
            headers: await _authHeaders,
          )
          .timeout(ApiConstants.receiveTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Sin conexión a internet. Verifica tu red.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Error inesperado: $e');
    }
  }

  static dynamic _handleResponse(http.Response response) {
    final body = utf8.decode(response.bodyBytes);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (body.isEmpty) return {};
      return jsonDecode(body);
    }

    String errorMessage = 'Error del servidor (${response.statusCode})';
    try {
      final errorBody = jsonDecode(body);
      errorMessage = errorBody['detail'] ?? errorMessage;
    } catch (_) {}

    throw ApiException(errorMessage, statusCode: response.statusCode);
  }
}
