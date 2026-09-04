const express = require("express");
const designController = require("../controllers/design-controller");
const authenticatedRequest = require("../middleware/auth-middleware");

const router = express.Router();

router.use(authenticatedRequest);

router.get("/", designController.getUserDesigns);
router.post("/", designController.saveDesign);
router.post("/:id/presence", designController.beatPresence);
router.get("/:id/presence", designController.listPresence);
router.get("/:id", designController.getUserDesignsByID);
router.delete("/:id", designController.deleteDesign);

module.exports = router;
