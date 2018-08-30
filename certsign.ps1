#reads from .\bootstrap.example.json
$Cert = (gi Cert:\CurrentUser\My\CERTTHUMBPRINT)
$file = (gc .\bootstrap.example.json)
$arr=[byte[]]([Text.Encoding]::UTF8.GetBytes($file))
$ms = New-Object System.IO.MemoryStream
$gzip = New-Object System.IO.Compression.GzipStream $ms, ([IO.Compression.CompressionMode]::Compress)
$gzip.Write( $arr, 0, $arr.Length )
$gzip.Close()
$ms.Close()
$compressed=$ms.ToArray()

[System.Reflection.Assembly]::LoadWithPartialName("System.Security") | Out-Null
$contentinfo = New-Object Security.Cryptography.Pkcs.ContentInfo -argumentList (,$compressed)
$signer = New-Object Security.Cryptography.Pkcs.CmsSigner
$signer.Certificate=$Cert
$signer.DigestAlgorithm.FriendlyName = "sha256"
$signer.SignedAttributes.Add((New-Object Security.Cryptography.Pkcs.Pkcs9SigningTime))
$ski=[System.Security.Cryptography.Pkcs.SubjectIdentifierType]::SubjectKeyIdentifier
$signer.SignerIdentifierType = $ski
$signer.IncludeOption = [System.Security.Cryptography.X509Certificates.X509IncludeOption]::EndCertOnly
$signedcms=New-Object Security.Cryptography.Pkcs.SignedCms($ski,$contentinfo,$false)
$signedcms.ComputeSignature($signer)
$base64string = [Convert]::ToBase64String($signedcms.Encode(),"InsertLineBreaks")

$string = . {
    "-----BEGIN CMS-----"
    $base64string
    "-----END CMS-----"
}

sc -Value $string -Path jit.signed

<#
Useful to write out a file for insertion into bootstrap.json from the certificate store
$certstring = . {
"-----BEGIN CERTIFICATE-----"
[System.Convert]::ToBase64String($cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert), "InsertLineBreaks")
"-----END CERTIFICATE-----"
}
sc -Value $certstring -Path test.cer
#>

