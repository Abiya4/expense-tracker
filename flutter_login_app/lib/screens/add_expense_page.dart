import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class AddExpensePage extends StatefulWidget {
  const AddExpensePage({super.key});

  @override
  State<AddExpensePage> createState() => _AddExpensePageState();
}

class _AddExpensePageState extends State<AddExpensePage> {
  final amountController = TextEditingController();
  String selectedCategory = "Food";

  final String baseUrl = "http://10.0.2.2:5000";

  final categories = [
    "Food",
    "Shopping",
    "Transport",
    "Entertainment",
    "Bills",
    "Health",
    "Other",
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050B18),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _header(),
              const SizedBox(height: 30),
              _glassCard(child: _amountInput()),
              const SizedBox(height: 20),
              _glassCard(child: _categoryDropdown()),
              const SizedBox(height: 30),
              _addButton(),
            ],
          ),
        ),
      ),
    );
  }

  // ---------------- HEADER ----------------
  Widget _header() {
    return Row(
      children: [
        IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        const Text(
          "Add Expense",
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
      ],
    );
  }

  // ---------------- AMOUNT ----------------
  Widget _amountInput() {
    return TextField(
      controller: amountController,
      keyboardType: TextInputType.number,
      style: const TextStyle(color: Colors.white, fontSize: 24),
      decoration: const InputDecoration(
        border: InputBorder.none,
        hintText: "₹ Amount",
        hintStyle: TextStyle(color: Colors.white38),
      ),
    );
  }

  // ---------------- CATEGORY ----------------
  Widget _categoryDropdown() {
    return DropdownButtonHideUnderline(
      child: DropdownButton<String>(
        value: selectedCategory,
        dropdownColor: const Color(0xFF0B1E2D),
        iconEnabledColor: Colors.white,
        items: categories
            .map(
              (c) => DropdownMenuItem(
                value: c,
                child: Text(c, style: const TextStyle(color: Colors.white)),
              ),
            )
            .toList(),
        onChanged: (val) {
          setState(() => selectedCategory = val!);
        },
      ),
    );
  }

  // ---------------- BUTTON ----------------
  Widget _addButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: addExpenseToServer,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF2FE6D1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        child: const Text(
          "Add Expense",
          style: TextStyle(
            color: Color(0xFF061417),
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  // ---------------- API ----------------
  Future<void> addExpenseToServer() async {
    if (amountController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter amount")),
      );
      return;
    }

    final response = await http.post(
      Uri.parse("$baseUrl/expenses"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "amount": double.parse(amountController.text),
        "category": selectedCategory,
      }),
    );

    if (response.statusCode == 201) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Expense added successfully"),
          backgroundColor: Colors.green,
        ),
      );
      amountController.clear();
      Navigator.pop(context);
    } else {
      final data = jsonDecode(response.body);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(data["message"] ?? "Failed to add expense"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // ---------------- GLASS ----------------
  Widget _glassCard({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.06),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withOpacity(0.08)),
          ),
          child: child,
        ),
      ),
    );
  }
}