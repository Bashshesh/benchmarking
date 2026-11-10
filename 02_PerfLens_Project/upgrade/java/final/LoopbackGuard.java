package perflens.finalstudy;

import java.net.SocketPermission;
import java.security.Permission;

/** The trusted JMH fork channel may use IPv4 loopback. Policy still checks each caller. */
@SuppressWarnings("removal")
public final class LoopbackGuard extends SecurityManager {
    private static void restrictSocket(Permission permission) {
        if (permission instanceof SocketPermission) {
            String destination = permission.getName();
            if (!destination.equals("127.0.0.1") && !destination.startsWith("127.0.0.1:")
                    && !destination.equals("localhost") && !destination.startsWith("localhost:")) {
                throw new SecurityException("Network destination outside JMH loopback: " + destination);
            }
        }
    }

    @Override
    public void checkPermission(Permission permission) {
        restrictSocket(permission);
        super.checkPermission(permission);
    }

    @Override
    public void checkPermission(Permission permission, Object context) {
        restrictSocket(permission);
        super.checkPermission(permission, context);
    }

    public static void main(String[] args) {
        SecurityManager manager = System.getSecurityManager();
        if (!(manager instanceof LoopbackGuard)) throw new AssertionError("Missing loopback guard");
        manager.checkPermission(new SocketPermission("127.0.0.1:9", "connect"));
        try {
            manager.checkPermission(new SocketPermission("192.0.2.1:9", "connect"));
            throw new AssertionError("Unexpected non-loopback permission");
        } catch (SecurityException expected) {
            System.out.println("Trusted loopback allowed; non-loopback denied");
        }
    }
}
