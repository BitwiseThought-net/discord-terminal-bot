module.exports = {
  // Only look for tests in the editor root, NOT in the dashboard subfolder
  testPathIgnorePatterns: [
    "/node_modules/",
    "<rootDir>/dashboard/"
  ],
  // Ensure it only picks up our backend tests
  testMatch: [
    "**/web-server.test.js"
  ],
  testEnvironment: "node"
};
