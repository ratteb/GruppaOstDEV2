-- Resource order: preserve the seven native entries, then iron, bauxite,
-- natural gas, rare earth minerals, titanium. Installed 1.18.3 resource docs
-- require this index-matched array when adding resources. New entries follow
-- the native industrial-resource zero-factory import threshold.
NDefines.NAI.MIN_FACTORIES_TO_WANT_TO_IMPORT = { 0, 0, 0, 0, 0, 0, 10, 0, 0, 0, 0, 0 }
