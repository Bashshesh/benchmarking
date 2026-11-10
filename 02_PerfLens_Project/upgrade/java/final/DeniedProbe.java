package perflens.finalstudy;

import java.io.FilePermission;
import java.net.SocketPermission;
import java.security.Permission;

public class DeniedProbe {
    @SuppressWarnings("removal")
    public static void main(String[] args) {
        SecurityManager manager = System.getSecurityManager();
        if (manager == null) throw new AssertionError("Missing security manager");
        Permission[] denied = {
            new FilePermission(args[0], "read"),
            new FilePermission(args[0], "write"),
            new FilePermission(args[1], "execute"),
            new SocketPermission("127.0.0.1:9", "connect"),
            new RuntimePermission("getenv.*"),
            new RuntimePermission("setSecurityManager"),
            new RuntimePermission("loadLibrary.*"),
            new java.lang.reflect.ReflectPermission("suppressAccessChecks")
        };
        for (Permission permission : denied) {
            try {
                manager.checkPermission(permission);
                throw new AssertionError("Unexpected grant " + permission);
            } catch (SecurityException expected) {
                System.out.println("denied " + permission);
            }
        }
    }
}
