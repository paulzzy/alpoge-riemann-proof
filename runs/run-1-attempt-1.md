# Probe run 1

Run: https://github.com/paulzzy/alpoge-riemann-proof/actions/runs/44767218575
Overall result of the probe jobs: success

## Probe: lib

```
runner: 4 cores, 15 GB RAM
lean: Lean (version 4.33.1, x86_64-unknown-linux-gnu, commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6, Release)
mathlib: 0df444a360eaa60ab8c11dca51a86af692955474 (clean checkout, prebuilt cache complete)
archive sha256: 9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc
```
| | |
|---|---|
| Modules expected | 836 |
| Modules compiled | 836 |
| Modules with errors | 0 |
| Build exit code | 0 |
| Wall time | 23.1 min |
| CPU time, all processes | 88.5 min |
| Peak memory, largest process | 9.78 GB |
| Source compiled | 5.43 MB |
| Build output on disk | 6.79 GB |
| CPU seconds per MB of source | 978 |
| Naive estimate, whole archive (1030.5 MB) | 280 CPU-hours, 1289 GB of output |

The estimate scales this probe linearly by source size. These files are the shallowest in the project, so treat it as a lower bound.

Slowest files:

- `Formalism.MahlerMeasure.MahlerMeasureProofs.PhiInt` 67 s
- `Formalism.LocalRingCardinality.DataLevel` 53 s
- `Formalism.PolynomialDimension.MultinomialDepth.PartnerM` 38 s
- `Formalism.PolynomialDimension.MultinomialDepth.SecondParameterSizeBoundsHolds` 37 s
- `Formalism.MahlerMeasure.MahlerMeasureProofs.GamLead` 36 s
- `Formalism.PadicSubsetSums.StableGradedCounts.IRRPrimeRecipSum` 35 s
- `Formalism.PolynomialDimension.MultinomialDepth.SecondParameterSlackBoundsHolds` 34 s
- `Formalism.MahlerMeasure.MahlerMeasureProofs.GamDeg` 28 s
- `Formalism.MahlerMeasure.MahlerMeasureProofs.MeanGam` 27 s
- `Formalism.HarderNarasimhan.HarderNarasimhanProofs.FrameLinearAlgebraFirst` 23 s

## Probe: sample

```
runner: 4 cores, 15 GB RAM
lean: Lean (version 4.33.1, x86_64-unknown-linux-gnu, commit 819816b2e0a3bf405af45ae5c7af2491d8f5bee6, Release)
mathlib: 0df444a360eaa60ab8c11dca51a86af692955474 (clean checkout, prebuilt cache complete)
archive sha256: 9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc
```
| | |
|---|---|
| Modules expected | 300 |
| Modules compiled | 300 |
| Modules with errors | 0 |
| Build exit code | 0 |
| Wall time | 7.5 min |
| CPU time, all processes | 28.7 min |
| Peak memory, largest process | 7.30 GB |
| Source compiled | 1.37 MB |
| Build output on disk | 2.40 GB |
| CPU seconds per MB of source | 1255 |
| Naive estimate, whole archive (1030.5 MB) | 359 CPU-hours, 1807 GB of output |

The estimate scales this probe linearly by source size. These files are the shallowest in the project, so treat it as a lower bound.

Slowest files:

- `Development.AbelianVarietyTheory.Definitions.NonGaloisDescent.PowerSeriesOneAddConstMulXMulInv` 23 s
- `Development.AbelianVarietyTheory.Definitions.QuasicoherentCohomology.MemSaturatedOrderIsoSubspaceSpanSymmApply` 21 s
- `Development.AbelianVarietyTheory.Proofs.FlagMeasures.DeepRegionExponents` 20 s
- `Formalism.LocalRingCardinality.SpanPowerMembership.UrRing` 15 s
- `Development.AbelianVarietyTheory.Proofs.CoherentCohomologyProofs.ExistsMvPolynomialOfIteratedBackwardDifferenceVa` 15 s
- `Development.AbelianVarietyTheory.Definitions.NonGaloisDescent.MapCSmulMulVec` 13 s
- `Formalism.LocalToGlobal.ProjectiveLattices.ArchimedeanQuadraticData.TieLDA` 11 s
- `Development.AutomorphicSpectrum.Proofs.BlockDecomposition.FourierTransformMatrixSpaceInvolution` 11 s
- `Development.AbelianVarietyTheory.Proofs.IwasawaDecomposition.FiniteDimensionalOfUniformlyAlmostInvariant` 11 s
- `Development.AbelianVarietyTheory.Proofs.InertiaEigenvalues.FinrankKerMapLeOfFirstOrderKernelExt` 11 s
