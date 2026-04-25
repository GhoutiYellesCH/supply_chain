import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";

import { AuthProvider } from "./src/auth";
import LoginScreen from "./src/screens/LoginScreen";
import DashboardScreen from "./src/screens/DashboardScreen";
import ScanScreen from "./src/screens/ScanScreen";
import SheepDetailsScreen from "./src/screens/SheepDetailsScreen";
import UpdateStatusScreen from "./src/screens/UpdateStatusScreen";
import RegisterSheepScreen from "./src/screens/RegisterSheepScreen";
import { theme } from "./src/theme";

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <StatusBar style="light" />
        <Stack.Navigator
          screenOptions={{
            headerStyle: { backgroundColor: theme.primary },
            headerTintColor: "#fff",
            headerTitleStyle: { fontWeight: "700" },
          }}
        >
          <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
          <Stack.Screen name="Dashboard" component={DashboardScreen} options={{ title: "Adhahi Tracker" }} />
          <Stack.Screen name="Scan" component={ScanScreen} options={{ title: "Scan QR" }} />
          <Stack.Screen name="SheepDetails" component={SheepDetailsScreen} options={{ title: "Sheep Timeline" }} />
          <Stack.Screen name="UpdateStatus" component={UpdateStatusScreen} options={{ title: "Update Status" }} />
          <Stack.Screen name="RegisterSheep" component={RegisterSheepScreen} options={{ title: "Register Sheep" }} />
        </Stack.Navigator>
      </NavigationContainer>
    </AuthProvider>
  );
}
