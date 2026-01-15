function generateUrl(base, pathPart = "") {
  if (!base) {
    throw new Error("base is required");
  }
  const normalized = base.endsWith("/") ? base.slice(0, -1) : base;
  const suffix = pathPart.startsWith("/") ? pathPart : `/${pathPart}`;
  return `${normalized}${suffix}`;
}

module.exports = {
  generateUrl,
};
