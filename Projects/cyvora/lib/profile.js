export async function ensureProfileRecords(supabase, user) {
  const { data: existingProfile } = await supabase
    .from("profiles")
    .select("id, company_id")
    .eq("id", user.id)
    .maybeSingle();

  if (existingProfile?.id) {
    return existingProfile;
  }

  const { data: company, error: companyError } = await supabase
    .from("companies")
    .insert({
      name:
        user.user_metadata?.company_name ||
        user.user_metadata?.full_name ||
        user.email?.split("@")[0] ||
        "Cyvora Client",
      phone: user.user_metadata?.phone || null,
    })
    .select("id")
    .single();

  if (companyError) {
    throw companyError;
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .insert({
      id: user.id,
      company_id: company.id,
      email: user.email,
      full_name:
        user.user_metadata?.full_name ||
        user.user_metadata?.company_name ||
        user.email?.split("@")[0] ||
        "Client Cyvora",
      phone: user.user_metadata?.phone || null,
    })
    .select("id, company_id")
    .single();

  if (profileError) {
    throw profileError;
  }

  return profile;
}
