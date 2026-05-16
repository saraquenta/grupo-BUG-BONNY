import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product_model.dart';
import 'storage_service.dart';

class ProductService {
  static const String baseUrl = 'http://127.0.0.1:8000/api';

  static Future<List<ProductModel>> getProducts() async {
    try {
      final token = await StorageService.getToken(); 

      final Map<String, String> headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }

      print('🚀 Consultando inventario a: $baseUrl/products/');
      final response = await http.get(
        Uri.parse('$baseUrl/products/'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final dynamic decodedBody = json.decode(response.body);
        
        List<dynamic> rawItems = [];

        // 🛠️ EXTRACCIÓN ULTRA SEGURA CONTRA PAGINACIÓN ROMPE-TIPOS:
        if (decodedBody is List) {
          // Si el backend responde una lista directa
          rawItems = decodedBody;
        } else if (decodedBody is Map && decodedBody.containsKey('items')) {
          // Si el backend responde paginado con {"items": [...]}, extraemos solo los items
          // Ignoramos 'page', 'size' y 'total' para que no rompan la app con sus tipos de datos
          rawItems = decodedBody['items'] as List? ?? [];
        } else if (decodedBody is Map) {
          // Por si los datos vienen envueltos en otra clave como 'data'
          rawItems = decodedBody['data'] as List? ?? [];
        }

        print('📥 Se encontraron ${rawItems.length} productos en bruto.');
        
        // Mapeamos usando el modelo blindado que ya tienes listo
        return rawItems.map((json) => ProductModel.fromJson(json)).toList();
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      print('❌ Fallo crítico en ProductService: $e');
      throw Exception('Error al cargar inventario: $e');
    }
  }

  // Dejamos listo el scanner M05 también con extracción directa por si acaso
  static Future<ProductModel?> getProductByCode(String code) async {
    try {
      final token = await StorageService.getToken();
      final Map<String, String> headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      if (token != null && token.isNotEmpty) {
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await http.get(
        Uri.parse('$baseUrl/products/by-code/$code'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final dynamic data = json.decode(response.body);
        if (data is Map<String, dynamic>) {
          return ProductModel.fromJson(data);
        }
      }
      return null;
    } catch (e) {
      print('Error en getProductByCode: $e');
      return null;
    }
  }
}