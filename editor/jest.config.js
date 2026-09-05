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
  testEnvironment: "node",
  // Cobertura output lets CI merge this coverage with the Python bot's
  // coverage.xml into a single combined coverage badge. junit output lets
  // CI merge test results with pytest's junit report into a single tests badge.
  coverageReporters: ["text", "cobertura"],
  reporters: [
    "default",
    ["jest-junit", { outputDirectory: ".", outputName: "junit.xml" }]
  ]
};
