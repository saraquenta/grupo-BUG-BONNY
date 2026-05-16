import 'package:flutter/material.dart';
import '../data/models/product_model.dart'; // Modelo de Producto
import '../data/services/product_service.dart';

class ProductProvider with ChangeNotifier {
  List<ProductModel> _products = [];
  List<ProductModel> _filteredProducts = [];
  List<String> _categories = ['Todas'];
  
  bool _isLoading = false;
  String _errorMessage = '';
  bool _filterByCriticalStock = false;
  String _selectedCategory = 'Todas';
  String _currentQuery = '';

  List<ProductModel> get products => _filteredProducts;
  List<String> get categories => _categories;
  bool get isLoading => _isLoading;
  String get errorMessage => _errorMessage;
  bool get filterByCriticalStock => _filterByCriticalStock;
  String get selectedCategory => _selectedCategory;

  Future<void> fetchProducts() async {
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      _products = await ProductService.getProducts();
      
      // Extrae categorías dinámicas únicas de la BD real
      final uniqueCats = _products.map((p) => p.category).toSet().toList();
      _categories = ['Todas', ...uniqueCats];

      _applyFilters();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void filterProducts(String query) {
    _currentQuery = query;
    _applyFilters();
  }

  void filterByCategory(String category) {
    _selectedCategory = category;
    _applyFilters();
  }

  void toggleCriticalStockFilter(bool value) {
    _filterByCriticalStock = value;
    _applyFilters();
  }

  void _applyFilters() {
    _filteredProducts = _products.where((product) {
      final matchesQuery = product.name.toLowerCase().contains(_currentQuery.toLowerCase()) ||
          product.code.toLowerCase().contains(_currentQuery.toLowerCase());
      
      final matchesCritical = !_filterByCriticalStock || product.isStockCritical;
      
      final matchesCategory = _selectedCategory == 'Todas' || product.category == _selectedCategory;

      return matchesQuery && matchesCritical && matchesCategory;
    }).toList();
    notifyListeners();
  }
}