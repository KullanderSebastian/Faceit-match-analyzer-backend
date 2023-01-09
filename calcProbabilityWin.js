const WIN_WEIGHT = 3;
const LOOSE_WEIGHT = 1;
const KR_WEIGHT = 4;

const TEAMKRWEIGHT = 500;
const TEAMELOWEIGHT  = 500;

const latestMatches = await this.faceit.GetLatestMatches(user.id, (depth)? 2000 : 50 : 0);
