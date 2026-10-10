"""Version & update algorithm for ServerCloud.

Update scheme (SemVer-like):
    MAJOR.MINOR.PATCH  (X.X.X)
      X.0.0  -> Global update        (major rewrite, breaking changes)
      0.X.0  -> Major update         (new features, backward compatible)
      0.0.X  -> Mini update          (fixes, small improvements)
"""

VERSION_MAJOR = 2   # X.0.0 — Global update
VERSION_MINOR = 0   # 0.X.0 — Major feature update
VERSION_PATCH = 0   # 0.0.X — Mini update (patch)
VERSION_SUFFIX = "-Beta-2"

VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}{VERSION_SUFFIX}"

UPDATE_ALGORITHM = """
Update algorithm:
  X.0.0  ->  Global update   (major rewrite, breaking changes)
  0.X.0  ->  Major update    (new features, backward compatible)
  0.0.X  ->  Mini update     (fixes, small improvements)
  Format:  X.X.X  (MAJOR.MINOR.PATCH)
"""


def bump(kind: str) -> str:
    """Return the next version string for a bump kind.

    kind: 'global' | 'major' | 'mini'
    """
    ma, mi, pa = VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH
    if kind == "global":
        return f"{ma + 1}.0.0"
    if kind == "major":
        return f"{ma}.{mi + 1}.0"
    if kind == "mini":
        return f"{ma}.{mi}.{pa + 1}"
    raise ValueError(f"unknown bump kind: {kind!r}")
