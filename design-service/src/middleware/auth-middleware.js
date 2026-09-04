const authenticatedRequest = (req, res, next) => {
    const userId = req.headers["x-user-id"];

    if (!userId) {
        return res.status(401).json({
            error: "Access denied! Please login to continue",
        });
    }

    req.user = {
        userId,
        email: req.headers["x-user-email"] || "",
        name: req.headers["x-user-name"] || "",
    };
    next();
};

module.exports = authenticatedRequest;
