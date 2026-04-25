import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { theme } from "../theme";

export default function ScanScreen({ navigation }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    if (!permission) return;
    if (!permission.granted) requestPermission();
  }, [permission]);

  const handleScanned = ({ data }) => {
    if (scanned) return;
    setScanned(true);
    if (!data) {
      Alert.alert("Empty QR");
      setScanned(false);
      return;
    }
    navigation.replace("SheepDetails", { tagId: data.trim() });
  };

  if (!permission?.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.msg}>Camera permission is required to scan QR codes.</Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.wrap}>
      <CameraView
        style={StyleSheet.absoluteFill}
        barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
        onBarcodeScanned={scanned ? undefined : handleScanned}
      />
      <View style={styles.overlay}>
        <View style={styles.frame} />
        <Text style={styles.hint}>Align the sheep QR code inside the frame</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: "#000" },
  overlay: { flex: 1, justifyContent: "center", alignItems: "center" },
  frame: {
    width: 240, height: 240, borderColor: theme.primary, borderWidth: 3, borderRadius: 16,
  },
  hint: { color: "#fff", marginTop: 16, fontWeight: "600" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24, backgroundColor: theme.bg },
  msg: { textAlign: "center", color: theme.text, marginBottom: 16 },
  btn: { backgroundColor: theme.primary, padding: 14, borderRadius: 10 },
  btnText: { color: "#fff", fontWeight: "700" },
});
