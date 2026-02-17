package com.example.flutter_login_app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel
import android.content.Context

class MainActivity: FlutterActivity() {
    private val EVENT_CHANNEL = "com.example.flutter_login_app/sms"
    private val METHOD_CHANNEL = "com.example.flutter_login_app/sms_methods"
    private var eventSink: EventChannel.EventSink? = null

    companion object {
        private var instance: MainActivity? = null

        fun sendSms(sender: String?, body: String?) {
            instance?.runOnUiThread {
                instance?.eventSink?.success(mapOf("sender" to sender, "body" to body))
            }
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        instance = this
        
        // Event Channel for Real-time SMS
        EventChannel(flutterEngine.dartExecutor.binaryMessenger, EVENT_CHANNEL).setStreamHandler(
            object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    eventSink = events
                }

                override fun onCancel(arguments: Any?) {
                    eventSink = null
                }
            }
        )

        // Method Channel for Pending SMS Sync
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, METHOD_CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "getPendingSms") {
                val prefs = getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                val pendingSms = prefs.getString("flutter.pending_sms", "[]")
                
                // Clear after reading
                if (pendingSms != "[]") {
                    prefs.edit().putString("flutter.pending_sms", "[]").apply()
                }
                
                result.success(pendingSms)
            } else {
                result.notImplemented()
            }
        }
    }
}
